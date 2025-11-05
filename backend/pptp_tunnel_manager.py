import subprocess,os,time,logging,re
logger=logging.getLogger("pptp_tunnel")
class PPTPTunnelManager:
 def __init__(self):self.active_tunnels={}
 def create_tunnel(self,node_id,node_ip,username,password):
  try:
   cfg=f"pptp_node_{node_id}";peer=f"/etc/ppp/peers/{cfg}";os.makedirs("/etc/ppp/peers",exist_ok=True)
   with open(peer,'w')as f:f.write(f'pty "pptp {node_ip} --nolaunchpppd"\nuser {username}\npassword {password}\nremotename PPTP\nnoauth\nnobsdcomp\nnodeflate\nnodefaultroute\nipparam {node_id}\npersist\nmaxfail 0\n')
   subprocess.Popen(["/usr/sbin/pppd","call",cfg,"logfile",f"/tmp/pptp_node_{node_id}.log"])
   logger.info(f"PPTP started for node {node_id}")
   time.sleep(8)
   ppp_iface=None;log_file=f"/tmp/pptp_node_{node_id}.log"
   if os.path.exists(log_file):
       with open(log_file,'r')as f:
           log_content=f.read();match=re.search(r'Connect: (ppp\d+)',log_content)
           if match:ppp_iface=match.group(1);logger.info(f"✅ Found ppp from log: {ppp_iface}")
   if not ppp_iface:
       try:
           ip_output=subprocess.check_output(["/usr/sbin/ip","addr","show"],text=True)
           for line in ip_output.split('\n'):
               if 'ppp' in line and 'UP' in line:
                   match=re.search(r'(ppp\d+)',line)
                   if match:ppp_iface=match.group(1);logger.info(f"✅ Found ppp from system: {ppp_iface}");break
       except:pass
   if not ppp_iface:logger.error(f"❌ Could not determine ppp for node {node_id}");return None
   from database import SessionLocal,Node
   db=SessionLocal();n=db.query(Node).filter(Node.id==node_id).first()
   if n:n.ppp_interface=ppp_iface;db.commit();logger.info(f"✅ Saved ppp to DB: {ppp_iface}")
   db.close()
   subprocess.run(["/usr/local/bin/link_socks_to_ppp.sh",str(1083+node_id),ppp_iface])
   ti={'interface':ppp_iface,'local_ip':'','remote_ip':'','pid':0,'node_ip':node_ip,'node_id':node_id}
   self.active_tunnels[node_id]=ti;logger.info(f"Tunnel OK: {ppp_iface}")
   return ti
  except Exception as e:logger.error(f"Error: {e}");import traceback;traceback.print_exc();return None
 def destroy_tunnel(self,nid):return True
pptp_tunnel_manager=PPTPTunnelManager()
