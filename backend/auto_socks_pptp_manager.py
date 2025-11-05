"""
Автоматический менеджер SOCKS/PPTP
- Автоматическая настройка routing при запуске
- Очистка мертвых процессов
- Самодиагностика и восстановление
"""
import subprocess
import logging
import time
import os

logger = logging.getLogger("auto_manager")

class AutoSOCKSPPTPManager:
    def __init__(self):
        self.active_routes = {}
        
    def cleanup_dead_processes(self):
        """Очистка зависших pppd процессов"""
        try:
            result = subprocess.run("ps aux | grep pppd | grep -v grep | wc -l", shell=True, capture_output=True, text=True)
            count = int(result.stdout.strip())
            if count > 50:
                logger.warning(f"⚠️ Слишком много pppd процессов: {count}, очищаю мертвые...")
                subprocess.run("pkill -9 -f 'pppd.*defunct'", shell=True)
                logger.info("✅ Мертвые процессы очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки: {e}")
    
    def setup_routing_auto(self, node_id, socks_port, ppp_interface):
        """Автоматическая настройка routing с проверкой"""
        try:
            # Проверка что интерфейс существует
            check = subprocess.run(f"ip a show {ppp_interface}", shell=True, capture_output=True)
            if check.returncode != 0:
                logger.error(f"❌ ppp интерфейс {ppp_interface} не существует!")
                return False
            
            # Вызов link_socks_to_ppp.sh
            result = subprocess.run(f"/usr/local/bin/link_socks_to_ppp.sh {socks_port} {ppp_interface}", 
                                  shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Routing настроен: port {socks_port} -> {ppp_interface}")
                self.active_routes[node_id] = {'port': socks_port, 'ppp': ppp_interface}
                return True
            else:
                logger.error(f"❌ Ошибка настройки routing: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка setup_routing_auto: {e}")
            return False
    
    def verify_routing(self, socks_port):
        """Проверка что routing настроен"""
        try:
            mark = socks_port - 1080
            table = 100 + mark
            
            # Проверка ip rule
            rule_check = subprocess.run(f"ip rule | grep 'fwmark {mark}'", shell=True, capture_output=True)
            if rule_check.returncode != 0:
                logger.warning(f"⚠️ Нет ip rule для порта {socks_port}")
                return False
            
            # Проверка routing table
            table_check = subprocess.run(f"ip route show table {table}", shell=True, capture_output=True, text=True)
            if "default" not in table_check.stdout:
                logger.warning(f"⚠️ Нет default route в table {table}")
                return False
            
            return True
        except:
            return False
    
    def auto_fix_routing(self, node_id, socks_port, ppp_interface):
        """Автоматическое исправление routing если сломан"""
        if not self.verify_routing(socks_port):
            logger.info(f"🔧 Исправляю routing для port {socks_port}")
            return self.setup_routing_auto(node_id, socks_port, ppp_interface)
        return True

# Глобальный экземпляр
auto_manager = AutoSOCKSPPTPManager()
