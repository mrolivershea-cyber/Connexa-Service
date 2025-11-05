#!/usr/bin/env python3
"""
OpenVPN Configuration Generator using pyOpenSSL
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from OpenSSL import crypto
import random
import string

class OVPNGenerator:
    """Generate OpenVPN configurations and certificates"""
    
    def __init__(self):
        self.ca_key = None
        self.ca_cert = None
        self.server_key = None
        self.server_cert = None
        self._generate_ca()
    
    def _generate_ca(self):
        """Generate Certificate Authority"""
        # Generate CA private key
        self.ca_key = crypto.PKey()
        self.ca_key.generate_key(crypto.TYPE_RSA, 2048)
        
        # Generate CA certificate
        self.ca_cert = crypto.X509()
        self.ca_cert.get_subject().C = "US"
        self.ca_cert.get_subject().ST = "Connexa"
        self.ca_cert.get_subject().L = "VPN"
        self.ca_cert.get_subject().O = "Connexa VPN"
        self.ca_cert.get_subject().OU = "CA"
        self.ca_cert.get_subject().CN = "Connexa-CA"
        
        self.ca_cert.set_serial_number(1000)
        self.ca_cert.gmtime_adj_notBefore(0)
        self.ca_cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1 year
        self.ca_cert.set_issuer(self.ca_cert.get_subject())
        self.ca_cert.set_pubkey(self.ca_key)
        
        # Add extensions
        self.ca_cert.add_extensions([
            crypto.X509Extension(b"basicConstraints", True, b"CA:TRUE"),
            crypto.X509Extension(b"keyUsage", True, b"keyCertSign, cRLSign"),
        ])
        
        self.ca_cert.sign(self.ca_key, 'sha256')
    
    def _generate_server_cert(self, server_ip: str):
        """Generate server certificate for given IP"""
        # Generate server private key
        self.server_key = crypto.PKey()
        self.server_key.generate_key(crypto.TYPE_RSA, 2048)
        
        # Generate server certificate
        self.server_cert = crypto.X509()
        self.server_cert.get_subject().C = "US"
        self.server_cert.get_subject().ST = "Connexa"
        self.server_cert.get_subject().L = "VPN"
        self.server_cert.get_subject().O = "Connexa VPN"
        self.server_cert.get_subject().OU = "Server"
        self.server_cert.get_subject().CN = server_ip
        
        self.server_cert.set_serial_number(random.randint(1001, 9999))
        self.server_cert.gmtime_adj_notBefore(0)
        self.server_cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1 year
        self.server_cert.set_issuer(self.ca_cert.get_subject())
        self.server_cert.set_pubkey(self.server_key)
        
        # Add extensions for server
        self.server_cert.add_extensions([
            crypto.X509Extension(b"basicConstraints", False, b"CA:FALSE"),
            crypto.X509Extension(b"keyUsage", False, b"digitalSignature, keyEncipherment"),
            crypto.X509Extension(b"extendedKeyUsage", False, b"serverAuth"),
            crypto.X509Extension(b"subjectAltName", False, f"IP:{server_ip}".encode()),
        ])
        
        self.server_cert.sign(self.ca_key, 'sha256')
    
    def _generate_client_cert(self, client_name: str):
        """Generate client certificate"""
        # Generate client private key
        client_key = crypto.PKey()
        client_key.generate_key(crypto.TYPE_RSA, 2048)
        
        # Generate client certificate
        client_cert = crypto.X509()
        client_cert.get_subject().C = "US"
        client_cert.get_subject().ST = "Connexa"
        client_cert.get_subject().L = "VPN"
        client_cert.get_subject().O = "Connexa VPN"
        client_cert.get_subject().OU = "Client"
        client_cert.get_subject().CN = client_name
        
        client_cert.set_serial_number(random.randint(2000, 9999))
        client_cert.gmtime_adj_notBefore(0)
        client_cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1 year
        client_cert.set_issuer(self.ca_cert.get_subject())
        client_cert.set_pubkey(client_key)
        
        # Add extensions for client
        client_cert.add_extensions([
            crypto.X509Extension(b"basicConstraints", False, b"CA:FALSE"),
            crypto.X509Extension(b"keyUsage", False, b"digitalSignature"),
            crypto.X509Extension(b"extendedKeyUsage", False, b"clientAuth"),
        ])
        
        client_cert.sign(self.ca_key, 'sha256')
        
        return client_key, client_cert
    
    def _generate_ta_key(self) -> str:
        """Generate TLS-Auth key (HMAC)"""
        # Generate random 2048-bit key for HMAC
        ta_key = "-----BEGIN OpenVPN Static key V1-----\n"
        
        for i in range(16):
            line = ''.join(random.choices('0123456789abcdef', k=32))
            ta_key += line + "\n"
        
        ta_key += "-----END OpenVPN Static key V1-----\n"
        return ta_key
    
    def generate_ovpn_config(self, server_ip: str, client_name: str, pptp_login: str) -> str:
        """
        Generate complete OVPN configuration for client
        """
        # Generate server cert if not exists
        if not self.server_cert:
            self._generate_server_cert(server_ip)
        
        # Generate client certificate
        client_key, client_cert = self._generate_client_cert(client_name)
        
        # Generate TLS-Auth key
        ta_key = self._generate_ta_key()
        
        # Convert certificates to PEM format
        ca_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, self.ca_cert).decode()
        client_cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, client_cert).decode()
        client_key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, client_key).decode()
        
        # Generate OVPN configuration
        ovpn_config = f"""# Connexa OpenVPN Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Server: {server_ip}
# Client: {client_name}

client
dev tun
proto udp
remote {server_ip} 1194
resolv-retry infinite
nobind
persist-key
persist-tun

# Security
cipher AES-256-GCM
auth SHA512
key-direction 1
remote-cert-tls server
tls-version-min 1.2

# Compression
compress lz4-v2
push "compress lz4-v2"

# Logging
verb 3
mute 10

# Certificates and Keys
<ca>
{ca_pem}</ca>

<cert>
{client_cert_pem}</cert>

<key>
{client_key_pem}</key>

<tls-auth>
{ta_key}</tls-auth>
"""
        
        return ovpn_config
    
    def generate_socks_credentials(self, node_ip: str, pptp_login: str) -> Dict:
        """
        Generate SOCKS proxy credentials based on PPTP data
        """
        # Generate SOCKS credentials based on PPTP login
        socks_login = f"socks_{pptp_login}"
        socks_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Use a deterministic port based on IP to avoid conflicts
        ip_parts = [int(x) for x in node_ip.split('.')]
        socks_port = 1080 + (ip_parts[2] * 256 + ip_parts[3]) % 8000  # Port range 1080-9080
        
        return {
            "ip": node_ip,
            "port": socks_port,
            "login": socks_login,
            "password": socks_password
        }

# Global generator instance
ovpn_generator = OVPNGenerator()