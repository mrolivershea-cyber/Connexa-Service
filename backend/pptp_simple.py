import subprocess
import os
import time
import logging
import re

logger = logging.getLogger("pptp_tunnel")

class PPTPTunnelManager:
    def __init__(self):
        self.active_tunnels = {}
        
    def create_tunnel(self, node_id, node_ip, username, password):
        try:
            cfg = f"pptp_node_{node_id}"
            peer = f"/etc/ppp/peers/{cfg}"
            os.makedirs("/etc/ppp/peers", exist_ok=True)
            
            with open(peer, 'w') as f:
                f.write(f'pty "pptp {node_ip} --nolaunchpppd"\n')
                f.write(f'user {username}\n')
                f.write(f'password {password}\n')
                f.write('remotename PPTP\n')
                f.write('noauth\n')
                f.write('nobsdcomp\n')
                f.write('nodeflate\n')
                f.write('nodefaultroute\n')
            
            p = subprocess.Popen(f"pppd call {cfg} logfile /tmp/pptp_node_{node_id}.log".split())
            logger.info(f"PPTP started PID {p.pid}")
            
            for i in range(15):
                time.sleep(1)
                r = subprocess.run("ip a | grep 'ppp[0-9]'", shell=True, capture_output=True, text=True)
                m = re.findall(r'(\d+):\s+(ppp\d+):', r.stdout)
                if m:
                    m.sort()
                    iface = m[-1][1]
                    ipr = subprocess.run(f"ip a s {iface}", shell=True, capture_output=True, text=True)
                    lm = re.search(r'inet\s+([\d.]+)', ipr.stdout)
                    rm = re.search(r'peer\s+([\d.]+)', ipr.stdout)
                    if lm and rm:
                        ti = {'interface': iface, 'local_ip': lm.group(1), 'remote_ip': rm.group(1), 'pid': p.pid, 'node_ip': node_ip, 'node_id': node_id}
                        self.active_tunnels[node_id] = ti
                        try:
                            from database import SessionLocal, Node
                            db = SessionLocal()
                            n = db.query(Node).filter(Node.id == node_id).first()
                            if n:
                                n.ppp_interface = iface
                                db.commit()
                            db.close()
                        except:
                            pass
                        logger.info(f"PPTP OK: {iface}")
                        return ti
            return None
        except:
            return None
    
    def destroy_tunnel(self, nid):
        try:
            if nid in self.active_tunnels:
                subprocess.run(f"kill -9 {self.active_tunnels[nid]['pid']}", shell=True)
                del self.active_tunnels[nid]
            return True
        except:
            return False

pptp_tunnel_manager = PPTPTunnelManager()
