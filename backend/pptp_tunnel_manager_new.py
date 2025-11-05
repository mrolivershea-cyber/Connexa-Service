import subprocess
import os
import time
import logging

logger = logging.getLogger("pptp_tunnel")


class PPTPTunnelManager:
    def __init__(self):
        self.active_tunnels = {}
    
    def wait_for_ppp_ready(self, ppp_interface, timeout=20):
        """
        Ждать, пока PPP интерфейс станет готовым
        Проверяет: наличие интерфейса + IP адрес
        """
        logger.info(f"Waiting for {ppp_interface} to become ready...")
        
        for attempt in range(timeout):
            try:
                # Проверяем, существует ли интерфейс
                result = subprocess.run(
                    f"ip a show {ppp_interface}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and "inet " in result.stdout:
                    logger.info(f"✅ {ppp_interface} is ready with IP")
                    return True
                
                logger.debug(f"⏳ {ppp_interface} not ready, attempt {attempt+1}/{timeout}")
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error checking {ppp_interface}: {e}")
                time.sleep(1)
        
        logger.error(f"❌ {ppp_interface} did not become ready after {timeout}s")
        return False
    
    def create_tunnel(self, node_id, node_ip, username, password):
        """
        Создать PPTP туннель с ожиданием готовности
        """
        try:
            cfg = f"pptp_node_{node_id}"
            peer = f"/etc/ppp/peers/{cfg}"
            os.makedirs("/etc/ppp/peers", exist_ok=True)
            
            # Создать конфигурацию pppd
            with open(peer, 'w') as f:
                f.write(f'''pty "pptp {node_ip} --nolaunchpppd"
user {username}
password {password}
remotename PPTP
noauth
nobsdcomp
nodeflate
nodefaultroute
ipparam {node_id}
persist
maxfail 0
''')
            
            # Запустить pppd
            subprocess.Popen(
                f"pppd call {cfg} logfile /tmp/pptp_node_{node_id}.log".split()
            )
            logger.info(f"PPTP started for node {node_id}")
            
            # Подождать, пока pppd создаст интерфейс
            time.sleep(3)
            
            # Получить ppp_interface из базы (его должен записать /etc/ppp/ip-up hook)
            from database import SessionLocal, Node
            db = SessionLocal()
            
            # Ждать до 15 секунд, пока появится ppp_interface в БД
            max_wait = 15
            for i in range(max_wait):
                db.expire_all()  # Обновить из БД
                node = db.query(Node).filter(Node.id == node_id).first()
                
                if node and node.ppp_interface:
                    ppp_interface = node.ppp_interface
                    logger.info(f"Found ppp_interface in DB: {ppp_interface}")
                    break
                
                logger.debug(f"Waiting for ppp_interface in DB ({i+1}/{max_wait})...")
                time.sleep(1)
            else:
                db.close()
                logger.error(f"ppp_interface not set in DB after {max_wait}s")
                return None
            
            # 🔹 НОВОЕ: Ждать готовности PPP интерфейса
            if not self.wait_for_ppp_ready(ppp_interface, timeout=20):
                db.close()
                logger.error(f"PPP interface {ppp_interface} not ready")
                return None
            
            # Настроить policy routing
            socks_port = 1083 + node_id
            result = subprocess.run(
                f"/usr/local/bin/link_socks_to_ppp.sh {socks_port} {ppp_interface}",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to setup routing: {result.stderr}")
                db.close()
                return None
            
            # Сохранить информацию о туннеле
            tunnel_info = {
                'interface': ppp_interface,
                'local_ip': '',
                'remote_ip': '',
                'pid': 0,
                'node_ip': node_ip,
                'node_id': node_id
            }
            self.active_tunnels[node_id] = tunnel_info
            
            logger.info(f"✅ Tunnel created: {ppp_interface}, routing configured")
            db.close()
            return tunnel_info
            
        except Exception as e:
            logger.error(f"Error creating tunnel for node {node_id}: {e}")
            return None
    
    def destroy_tunnel(self, node_id):
        """Уничтожить PPTP туннель"""
        try:
            # Убить pppd процесс
            subprocess.run(
                f"pkill -f 'pppd call pptp_node_{node_id}'",
                shell=True
            )
            
            # Удалить из активных
            if node_id in self.active_tunnels:
                del self.active_tunnels[node_id]
            
            logger.info(f"Tunnel destroyed for node {node_id}")
            return True
        except Exception as e:
            logger.error(f"Error destroying tunnel: {e}")
            return False


pptp_tunnel_manager = PPTPTunnelManager()
