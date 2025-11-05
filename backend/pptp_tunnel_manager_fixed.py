import subprocess
import os
import time
import logging
import re
from typing import Dict, Optional

logger = logging.getLogger("pptp_tunnel")

class PPTPTunnelManager:
    def __init__(self):
        self.active_tunnels: Dict[int, Dict] = {}
        
    def create_tunnel(self, node_id: int, node_ip: str, username: str, password: str) -> Optional[Dict]:
        try:
            logger.info(f"Creating PPTP tunnel to {node_ip} for node {node_id}")
            
            config_name = f"pptp_node_{node_id}"
            peer_file = f"/etc/ppp/peers/{config_name}"
            os.makedirs("/etc/ppp/peers", exist_ok=True)
            
            with open(peer_file, 'w') as f:
                f.write(f'''pty "pptp {node_ip} --nolaunchpppd"
user {username}
password {password}
remotename PPTP
lock
noauth
nobsdcomp
nodeflate
refuse-eap
refuse-pap
refuse-chap
require-mschap-v2
require-mppe-128
nodefaultroute
persist
maxfail 0
''')
            
            cmd = f"pppd call {config_name} updetach logfile /tmp/pptp_node_{node_id}.log"
            logger.info(f"Starting PPTP: {cmd}")
            
            process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"PPTP process started with PID {process.pid}")
            
            for i in range(20):
                time.sleep(1)
                poll = process.poll()
                if poll is not None and poll != 0:
                    logger.error(f"PPTP process died with code {poll}")
                    try:
                        with open(f'/tmp/pptp_node_{node_id}.log', 'r') as f:
                            logger.error(f"Log: {f.read()[-300:]}")
                    except: pass
                    return None
                
                result = subprocess.run("ip addr show | grep -E 'ppp[0-9]+'", shell=True, capture_output=True, text=True)
                if result.stdout:
                    ppp_list = re.findall(r'(\d+):\s+(ppp\d+):', result.stdout)
                    if ppp_list:
                        ppp_list.sort(key=lambda x: int(x[0]))
                        interface = ppp_list[-1][1]
                        
                        ip_result = subprocess.run(f"ip addr show {interface}", shell=True, capture_output=True, text=True)
                        local_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
                        remote_match = re.search(r'peer\s+(\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
                        
                        if local_match and remote_match:
                            local_ip = local_match.group(1)
                            remote_ip = remote_match.group(1)
                            
                            tunnel_info = {
                                'interface': interface,
                                'local_ip': local_ip,
                                'remote_ip': remote_ip,
                                'pid': process.pid,
                                'node_ip': node_ip,
                                'node_id': node_id
                            }
                            
                            self.active_tunnels[node_id] = tunnel_info
                            
                            try:
                                from database import SessionLocal, Node as DBNode
                                db = SessionLocal()
                                db_node = db.query(DBNode).filter(DBNode.id == node_id).first()
                                if db_node:
                                    db_node.ppp_interface = interface
                                    db.commit()
                                db.close()
                            except: pass
                            
                            logger.info(f"PPTP tunnel OK: {interface} ({local_ip} -> {remote_ip})")
                            return tunnel_info
            
            logger.error(f"PPTP tunnel timeout for node {node_id}")
            try:
                process.kill()
            except: pass
            return None
            
        except Exception as e:
            logger.error(f"Error creating PPTP tunnel: {e}")
            return None
    
    def destroy_tunnel(self, node_id: int) -> bool:
        try:
            if node_id not in self.active_tunnels:
                return True
            
            tunnel_info = self.active_tunnels[node_id]
            pid = tunnel_info['pid']
            
            subprocess.run(f"kill {pid}", shell=True, timeout=5)
            time.sleep(1)
            subprocess.run(f"kill -9 {pid}", shell=True, timeout=5)
            
            del self.active_tunnels[node_id]
            return True
        except:
            return False

pptp_tunnel_manager = PPTPTunnelManager()
