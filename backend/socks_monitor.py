"""
SOCKS Monitoring System for Connexa Admin Panel
Monitors SOCKS services every 30 seconds, handles failures, manages proxy file
"""
import asyncio
import logging
import time
import os
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from database import SessionLocal, Node
from socks_server import socks_proxy, stop_socks_service
import socket

logger = logging.getLogger("socks_monitor")

class SOCKSMonitor:
    """SOCKS Service Monitoring System"""
    
    def __init__(self):
        self.running = False
        self.monitor_task = None
        self.last_proxy_file_update = None
        self.proxy_file_path = "/tmp/active_socks_proxies.txt"
        
    def start_monitoring(self):
        """Start SOCKS monitoring service"""
        if self.running:
            logger.warning("SOCKS monitor already running")
            return
            
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("🔍 SOCKS monitoring service started - checking every 30 seconds")
    
    def stop_monitoring(self):
        """Stop SOCKS monitoring service"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
        logger.info("🛑 SOCKS monitoring service stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._check_socks_health()
                await self._update_proxy_file()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in SOCKS monitor loop: {e}")
                await asyncio.sleep(10)  # Short delay on error
    
    async def _check_socks_health(self):
        """Check health of all SOCKS services"""
        try:
            db = SessionLocal()
            
            # Get all online SOCKS nodes
            online_socks_nodes = db.query(Node).filter(
                Node.status == "online",
                Node.socks_ip.isnot(None),
                Node.socks_port.isnot(None)
            ).all()
            
            for node in online_socks_nodes:
                try:
                    # Check if SOCKS server is actually running
                    if not self._is_socks_port_active(node.socks_port):
                        logger.warning(f"⚠️ SOCKS server on port {node.socks_port} (node {node.id}) not responding")
                        await self._handle_socks_failure(node, db)
                    
                    # Skip node reachability check for now - PPTP/SSH nodes may not respond to ping
                    # TODO: Implement proper connectivity check through PPTP/SSH tunnel
                    # elif not self._is_node_reachable(node.ip):
                    #     logger.warning(f"⚠️ Target node {node.ip} (node {node.id}) unreachable")
                    #     await self._handle_node_unreachable(node, db)
                    
                except Exception as e:
                    logger.error(f"Error checking SOCKS health for node {node.id}: {e}")
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"Error in SOCKS health check: {e}")
    
    def _is_socks_port_active(self, port: int) -> bool:
        """Check if SOCKS server port is active"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _is_node_reachable(self, node_ip: str) -> bool:
        """Check if target node is reachable via ping"""
        try:
            import subprocess
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '5', node_ip], 
                capture_output=True, 
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def _handle_socks_failure(self, node: Node, db: Session):
        """Handle SOCKS server failure"""
        try:
            logger.error(f"🚨 SOCKS server failure detected for node {node.id}, stopping service")
            
            # Stop the failed SOCKS service
            stop_socks_service(node.id)
            
            # Clear SOCKS data and revert status to ping_ok (safe fallback)
            node.socks_ip = None
            node.socks_port = None
            node.socks_login = None
            node.socks_password = None
            node.status = "ping_ok"  # Automatic failure -> safe fallback to ping_ok
            node.previous_status = None
            node.last_update = datetime.utcnow()
            
            logger.info(f"🔄 Node {node.id} reverted to ping_ok status due to SOCKS failure")
            
        except Exception as e:
            logger.error(f"Error handling SOCKS failure for node {node.id}: {e}")
    
    async def _handle_node_unreachable(self, node: Node, db: Session):
        """Handle target node unreachable"""
        try:
            logger.warning(f"⚠️ Target node {node.ip} (node {node.id}) unreachable, stopping SOCKS")
            
            # Stop SOCKS service for unreachable node
            stop_socks_service(node.id)
            
            # Clear SOCKS data and revert to ping_ok
            node.socks_ip = None
            node.socks_port = None
            node.socks_login = None
            node.socks_password = None
            node.status = "ping_ok"  # Node unreachable -> ping_ok
            node.previous_status = None
            node.last_update = datetime.utcnow()
            
            logger.info(f"🔄 Node {node.id} reverted to ping_ok due to target unreachable")
            
        except Exception as e:
            logger.error(f"Error handling unreachable node {node.id}: {e}")
    
    async def _update_proxy_file(self):
        """Update active proxies text file"""
        try:
            db = SessionLocal()
            
            # Get active SOCKS proxies
            active_proxies = db.query(Node).filter(
                Node.status == "online",
                Node.socks_ip.isnot(None),
                Node.socks_port.isnot(None),
                Node.socks_login.isnot(None),
                Node.socks_password.isnot(None)
            ).all()
            
            # Generate proxy file content
            proxy_lines = []
            proxy_lines.append("# Активные SOCKS прокси - Connexa Admin Panel")
            proxy_lines.append(f"# Обновлено: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            proxy_lines.append(f"# Всего активных: {len(active_proxies)}")
            proxy_lines.append("")
            
            if active_proxies:
                for node in active_proxies:
                    # Формат: IP:PORT:LOGIN:PASS (по требованию пользователя)
                    proxy_line = f"{node.socks_ip}:{node.socks_port}:{node.socks_login}:{node.socks_password}"
                    proxy_lines.append(f"{proxy_line}  # Node {node.id} -> {node.ip} ({node.city}, {node.country})")
            else:
                proxy_lines.append("# Нет активных SOCKS прокси")
            
            # Write to file
            proxy_content = "\n".join(proxy_lines)
            with open(self.proxy_file_path, 'w', encoding='utf-8') as f:
                f.write(proxy_content)
            
            self.last_proxy_file_update = datetime.utcnow()
            
            # Log update if proxies exist
            if active_proxies:
                logger.debug(f"📄 Proxy file updated: {len(active_proxies)} active SOCKS services")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error updating proxy file: {e}")
    
    def get_proxy_file_content(self) -> str:
        """Get current proxy file content"""
        try:
            if os.path.exists(self.proxy_file_path):
                with open(self.proxy_file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "# Файл прокси еще не создан\n# Запустите SOCKS сервисы для генерации файла"
        except Exception as e:
            logger.error(f"Error reading proxy file: {e}")
            return f"# Ошибка чтения файла прокси: {e}"
    
    def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics"""
        return {
            "monitoring_active": self.running,
            "last_check": datetime.utcnow().isoformat(),
            "proxy_file_path": self.proxy_file_path,
            "last_proxy_file_update": self.last_proxy_file_update.isoformat() if self.last_proxy_file_update else None,
            "proxy_file_exists": os.path.exists(self.proxy_file_path)
        }


# Global SOCKS monitor instance
socks_monitor = SOCKSMonitor()


def start_socks_monitoring():
    """Start SOCKS monitoring service"""
    socks_monitor.start_monitoring()


def stop_socks_monitoring():
    """Stop SOCKS monitoring service"""
    socks_monitor.stop_monitoring()


def get_proxy_file_content() -> str:
    """Get proxy file content"""
    return socks_monitor.get_proxy_file_content()


def get_monitoring_stats() -> Dict:
    """Get monitoring statistics"""
    return socks_monitor.get_monitoring_stats()