"""
SOCKS5 Server with Traffic Masking for Connexa Admin Panel
Architecture: Client → SOCKS(admin server) → Node(PPTP/SSH/OVPN) → Internet
"""
import asyncio
import socket
import struct
import logging
import secrets
import time
import random
import ssl
import os
import select
import threading
from typing import Dict, Set, Optional, Tuple
from datetime import datetime
from threading import Thread, Lock
import subprocess
import json

logger = logging.getLogger("socks_server")

# Import PPTP tunnel manager
from pptp_tunnel_manager import pptp_tunnel_manager

class SOCKSProxy:
    """SOCKS5 Proxy Server with Traffic Masking"""
    
    def __init__(self):
        self.running_servers: Dict[int, 'SOCKSServer'] = {}
        self.active_connections: Set[str] = set()
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'bytes_transferred': 0
        }
        self.stats_lock = Lock()
        
    def start_socks_for_node(self, node_id: int, node_ip: str, port: int, 
                           username: str, password: str, masking_config: dict) -> bool:
        """Start SOCKS5 server for specific node"""
        try:
            if node_id in self.running_servers:
                logger.warning(f"SOCKS server already running for node {node_id}")
                return True
                
            server = SOCKSServer(
                node_id=node_id,
                node_ip=node_ip,
                port=port,
                username=username,
                password=password,
                masking_config=masking_config,
                stats_callback=self._update_stats
            )
            
            if server.start():
                self.running_servers[node_id] = server
                logger.info(f"✅ SOCKS5 server started for node {node_id} on port {port}")
                return True
            else:
                logger.error(f"❌ Failed to start SOCKS5 server for node {node_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting SOCKS server for node {node_id}: {e}")
            return False
    
    def stop_socks_for_node(self, node_id: int) -> bool:
        """Stop SOCKS5 server for specific node"""
        try:
            if node_id not in self.running_servers:
                logger.warning(f"No SOCKS server running for node {node_id}")
                return True
                
            server = self.running_servers[node_id]
            server.stop()
            del self.running_servers[node_id]
            
            logger.info(f"🛑 SOCKS5 server stopped for node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping SOCKS server for node {node_id}: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get current SOCKS statistics"""
        with self.stats_lock:
            return {
                'online_socks': len(self.running_servers),
                'total_tunnels': len(self.running_servers),
                'active_connections': self.connection_stats['active_connections'],
                'total_connections': self.connection_stats['total_connections'],
                'bytes_transferred': self.connection_stats['bytes_transferred']
            }
    
    def _update_stats(self, event: str, data: dict = None):
        """Update connection statistics"""
        with self.stats_lock:
            if event == 'connection_start':
                self.connection_stats['active_connections'] += 1
                self.connection_stats['total_connections'] += 1
            elif event == 'connection_end':
                self.connection_stats['active_connections'] -= 1
            elif event == 'bytes_transferred':
                self.connection_stats['bytes_transferred'] += data.get('bytes', 0)


class SOCKSServer:
    """Individual SOCKS5 Server Instance with Traffic Masking"""
    
    def __init__(self, node_id: int, node_ip: str, port: int, username: str, 
                 password: str, masking_config: dict, stats_callback=None):
        self.node_id = node_id
        self.node_ip = node_ip
        self.port = port
        self.username = username
        self.password = password
        self.masking_config = masking_config
        self.stats_callback = stats_callback
        
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.server_thread: Optional[Thread] = None
        self.active_connections: Set[Thread] = set()
        
        # Traffic masking components
        self.obfuscation_key = secrets.token_bytes(32) if masking_config.get('obfuscation') else None
        self.timing_randomizer = TimingRandomizer() if masking_config.get('timing_randomization') else None
        self.http_imitator = HTTPImitator() if masking_config.get('http_imitation') else None
        
    def start(self) -> bool:
        """Start the SOCKS5 server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(100)  # Support up to 100 concurrent connections
            
            self.running = True
            self.server_thread = Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            logger.info(f"SOCKS5 server started on port {self.port} for node {self.node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start SOCKS5 server on port {self.port}: {e}")
            return False
    
    def stop(self):
        """Stop the SOCKS5 server"""
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        # Close active connections
        for conn_thread in list(self.active_connections):
            # Connections will timeout and close naturally
            pass
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
    
    def _server_loop(self):
        """Main server loop"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                logger.debug(f"New connection from {addr} to SOCKS server port {self.port}")
                
                # Handle connection in separate thread
                conn_thread = Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                self.active_connections.add(conn_thread)
                conn_thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection on port {self.port}: {e}")
                break
    
    def _handle_client(self, client_socket: socket.socket, addr: Tuple):
        """Handle individual client connection"""
        try:
            if self.stats_callback:
                self.stats_callback('connection_start')
            
            # Apply timing randomization for masking
            if self.timing_randomizer:
                self.timing_randomizer.random_delay()
            
            # SOCKS5 handshake
            if not self._socks5_handshake(client_socket):
                return
            
            # SOCKS5 authentication
            if not self._socks5_auth(client_socket):
                return
            
            # SOCKS5 connection request
            target_host, target_port = self._socks5_request(client_socket)
            if not target_host:
                return
            
            # Connect through node (PPTP/SSH/OVPN tunnel)
            upstream_socket = self._connect_through_node(target_host, target_port)
            if not upstream_socket:
                self._send_socks5_response(client_socket, 0x01)  # General failure
                return
            
            # Send success response
            self._send_socks5_response(client_socket, 0x00)  # Success
            
            # Start data relay with masking
            self._relay_data(client_socket, upstream_socket)
            
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            client_socket.close()
            if self.stats_callback:
                self.stats_callback('connection_end')
            
            # Remove from active connections
            current_thread = threading.current_thread()
            if current_thread in self.active_connections:
                self.active_connections.remove(current_thread)
    
    def _socks5_handshake(self, client_socket: socket.socket) -> bool:
        """SOCKS5 handshake phase"""
        try:
            data = client_socket.recv(256)
            if not data or len(data) < 3:
                return False
            
            version, nmethods = struct.unpack('!BB', data[:2])
            if version != 5:
                return False
            
            methods = data[2:2+nmethods]
            
            # We support username/password auth (method 2)
            if b'\x02' in methods:
                client_socket.send(b'\x05\x02')  # SOCKS5, username/password auth
                return True
            else:
                client_socket.send(b'\x05\xff')  # No acceptable methods
                return False
                
        except Exception as e:
            logger.error(f"SOCKS5 handshake error: {e}")
            return False
    
    def _socks5_auth(self, client_socket: socket.socket) -> bool:
        """SOCKS5 authentication phase"""
        try:
            data = client_socket.recv(256)
            if not data or len(data) < 2:
                return False
            
            version, username_len = struct.unpack('!BB', data[:2])
            if version != 1:
                return False
            
            username = data[2:2+username_len].decode('utf-8')
            password_len = data[2+username_len]
            password = data[3+username_len:3+username_len+password_len].decode('utf-8')
            
            # Verify credentials
            if username == self.username and password == self.password:
                client_socket.send(b'\x01\x00')  # Success
                return True
            else:
                client_socket.send(b'\x01\x01')  # Failure
                logger.warning(f"Authentication failed for user '{username}' on port {self.port}")
                return False
                
        except Exception as e:
            logger.error(f"SOCKS5 authentication error: {e}")
            return False
    
    def _socks5_request(self, client_socket: socket.socket) -> Tuple[Optional[str], Optional[int]]:
        """Handle SOCKS5 connection request"""
        try:
            data = client_socket.recv(256)
            if not data or len(data) < 4:
                return None, None
            
            version, cmd, reserved, atyp = struct.unpack('!BBBB', data[:4])
            
            if version != 5 or cmd != 1:  # Only support CONNECT command
                self._send_socks5_response(client_socket, 0x07)  # Command not supported
                return None, None
            
            # Parse destination address
            if atyp == 1:  # IPv4
                addr = socket.inet_ntoa(data[4:8])
                port = struct.unpack('!H', data[8:10])[0]
            elif atyp == 3:  # Domain name
                addr_len = data[4]
                addr = data[5:5+addr_len].decode('utf-8')
                port = struct.unpack('!H', data[5+addr_len:7+addr_len])[0]
            else:
                self._send_socks5_response(client_socket, 0x08)  # Address type not supported
                return None, None
            
            return addr, port
            
        except Exception as e:
            logger.error(f"SOCKS5 request error: {e}")
            return None, None
    
    def _send_socks5_response(self, client_socket: socket.socket, status: int):
        """Send SOCKS5 response"""
        try:
            # Response format: VER REP RSV ATYP BND.ADDR BND.PORT
            response = struct.pack('!BBBB', 5, status, 0, 1)  # IPv4
            response += socket.inet_aton('0.0.0.0')  # Bind address
            response += struct.pack('!H', 0)  # Bind port
            client_socket.send(response)
        except Exception as e:
            logger.error(f"Error sending SOCKS5 response: {e}")
    
    def _connect_through_node(self, target_host: str, target_port: int) -> Optional[socket.socket]:
        """Connect to target through the node's PPTP tunnel"""
        try:
            # Get PPTP tunnel info for this node
            tunnel_info = pptp_tunnel_manager.get_tunnel_info(self.node_id)
            
            if not tunnel_info:
                logger.error(f"❌ No PPTP tunnel found for node {self.node_id}")
                return None
            
            interface = tunnel_info['interface']
            local_ip = tunnel_info['local_ip']
            
            logger.debug(f"🔗 Connecting to {target_host}:{target_port} through PPTP tunnel {interface}")
            
            # Create socket and bind to PPTP tunnel interface IP
            upstream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upstream_socket.settimeout(30)
            
            # Bind to local IP of PPTP tunnel to force routing through it
            try:
                upstream_socket.bind((local_ip, 0))
            except Exception as bind_error:
                logger.warning(f"⚠️ Could not bind to {local_ip}: {bind_error}, using default routing")
            
            upstream_socket.connect((target_host, target_port))
            
            logger.debug(f"✅ Connected to {target_host}:{target_port} through PPTP tunnel {interface}")
            return upstream_socket
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to {target_host}:{target_port} through node {self.node_id}: {e}")
            return None
    
    def _relay_data(self, client_socket: socket.socket, upstream_socket: socket.socket):
        """Relay data between client and upstream with masking"""
        try:
            sockets = [client_socket, upstream_socket]
            bytes_transferred = 0
            
            while True:
                ready, _, _ = select.select(sockets, [], [], 30)  # 30 second timeout
                
                if not ready:
                    break  # Timeout
                
                for sock in ready:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            return  # Connection closed
                        
                        # Apply traffic masking
                        masked_data = self._apply_masking(data)
                        
                        # Send to the other socket
                        other_sock = upstream_socket if sock == client_socket else client_socket
                        other_sock.send(masked_data)
                        
                        bytes_transferred += len(data)
                        
                        # Apply timing randomization
                        if self.timing_randomizer:
                            self.timing_randomizer.micro_delay()
                            
                    except Exception as e:
                        logger.debug(f"Connection closed during relay: {e}")
                        return
            
            # Update statistics
            if self.stats_callback:
                self.stats_callback('bytes_transferred', {'bytes': bytes_transferred})
                
        except Exception as e:
            logger.error(f"Error in data relay: {e}")
        finally:
            upstream_socket.close()
    
    def _apply_masking(self, data: bytes) -> bytes:
        """Apply traffic masking techniques"""
        masked_data = data
        
        # Obfuscation
        if self.obfuscation_key and self.masking_config.get('obfuscation'):
            masked_data = self._obfuscate_data(masked_data)
        
        # HTTP imitation
        if self.http_imitator and self.masking_config.get('http_imitation'):
            masked_data = self.http_imitator.wrap_data(masked_data)
        
        return masked_data
    
    def _obfuscate_data(self, data: bytes) -> bytes:
        """Simple XOR obfuscation"""
        try:
            key_len = len(self.obfuscation_key)
            return bytes(data[i] ^ self.obfuscation_key[i % key_len] for i in range(len(data)))
        except Exception:
            return data  # Return original data if obfuscation fails


class TimingRandomizer:
    """Randomize timing patterns to avoid DPI detection"""
    
    def random_delay(self):
        """Add random delay (10-100ms)"""
        delay = random.uniform(0.01, 0.1)
        time.sleep(delay)
    
    def micro_delay(self):
        """Add micro delay (1-10ms)"""
        delay = random.uniform(0.001, 0.01)
        time.sleep(delay)


class HTTPImitator:
    """Imitate HTTP/HTTPS traffic patterns"""
    
    def __init__(self):
        self.http_headers = [
            b"GET /api/v1/data HTTP/1.1\r\nHost: api.example.com\r\n",
            b"POST /upload HTTP/1.1\r\nHost: upload.service.com\r\n",
            b"PUT /file.json HTTP/1.1\r\nHost: cdn.example.net\r\n"
        ]
    
    def wrap_data(self, data: bytes) -> bytes:
        """Wrap data in HTTP-like headers (simplified)"""
        if len(data) < 100:  # Only for small packets
            header = random.choice(self.http_headers)
            return header + b"Content-Length: " + str(len(data)).encode() + b"\r\n\r\n" + data
        return data


# Global SOCKS proxy instance
socks_proxy = SOCKSProxy()


def start_socks_service(node_id: int, node_ip: str, port: int, username: str, 
                       password: str, masking_config: dict) -> bool:
    """Start SOCKS5 service for a node"""
    return socks_proxy.start_socks_for_node(
        node_id=node_id,
        node_ip=node_ip, 
        port=port,
        username=username,
        password=password,
        masking_config=masking_config
    )


def stop_socks_service(node_id: int) -> bool:
    """Stop SOCKS5 service for a node"""
    return socks_proxy.stop_socks_for_node(node_id)


def get_socks_stats() -> dict:
    """Get SOCKS statistics"""
    return socks_proxy.get_stats()


if __name__ == "__main__":
    # Test SOCKS server
    logging.basicConfig(level=logging.DEBUG)
    
    masking_config = {
        'obfuscation': True,
        'http_imitation': True, 
        'timing_randomization': True,
        'tunnel_encryption': True
    }
    
    success = start_socks_service(
        node_id=999,
        node_ip="8.8.8.8",
        port=1080,
        username="test_user",
        password="test_password",
        masking_config=masking_config
    )
    
    if success:
        print("✅ Test SOCKS server started on port 1080")
        print("Test with: curl --socks5 test_user:test_password@localhost:1080 http://httpbin.org/ip")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_socks_service(999)
            print("🛑 Test server stopped")