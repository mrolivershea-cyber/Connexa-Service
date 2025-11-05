import subprocess,os,time,logging,re
logger=logging.getLogger("pptp_tunnel")
class PPTPTunnelManager:
 def __init__(self):self.active_tunnels={}
 def create_tunnel(self,node_id,node_ip,username,password):
  try:
   cfg=f"pptp_node_{node_id}";peer=f"/etc/ppp/peers/{cfg}";os.makedirs("/etc/ppp/peers",exist_ok=True)
   with open(peer,'w')as f:f.write(f'pty "pptp {node_ip} --nolaunchpppd"\nuser {username}\npassword {password}\nremotemname PPTP\nnoauth\nnobsdcomp\nnodeflate\nnodefaultroute\nipparam {node_id}\npersist\nmaxfail 0\n')
   p=subprocess.Popen(f"pppd call {cfg} logfile /tmp/pptp_node_{node_id}.log".split())
   logger.info(f"PID {p.pid}")
   time.sleep(8)
   from database import SessionLocal,Node
   db=SessionLocal();n=db.query(Node).filter(Node.id==node_id).first()
   if n and n.ppp_interface:
    ti={'interface':n.ppp_interface,'local_ip':'','remote_ip':'','pid':p.pid,'node_ip':node_ip,'node_id':node_id}
    self.active_tunnels[node_id]=ti
    logger.info(f"OK from DB: {n.ppp_interface}")
    subprocess.run(f"/usr/local/bin/link_socks_to_ppp.sh {1083+node_id} {n.ppp_interface}",shell=True)
    db.close()
    return ti
   db.close()
   return None
  except:return None
 def destroy_tunnel(self,nid):return True
pptp_tunnel_manager=PPTPTunnelManager()
