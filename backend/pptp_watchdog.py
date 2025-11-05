"""
PPTP Watchdog - Мягкая проверка здоровья PPTP туннелей
Логика: Если PPTP туннель онлайн -> SOCKS работает
        Если PPTP туннель упал -> SOCKS не работает
"""
import os
import sys
import time
import subprocess
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PPTP_WATCHDOG - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pptp_watchdog")

# Параметры из .env
WATCHDOG_CHECK_INTERVAL = int(os.environ.get('WATCHDOG_CHECK_INTERVAL', 180))  # 3 минуты
WATCHDOG_PPTP_RETRIES = int(os.environ.get('WATCHDOG_PPTP_RETRIES', 3))
WATCHDOG_RETRY_DELAY = int(os.environ.get('WATCHDOG_RETRY_DELAY', 30))

# База данных
DB_PATH = os.environ.get('CONNEXA_DB', '/app/backend/connexa.db')
engine = create_engine(f'sqlite:///{DB_PATH}', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def check_pptp_tunnel(node_id: int, ppp_interface: str) -> bool:
    """
    Проверить здоровье PPTP туннеля
    Проверяет:
    1. Процесс pppd жив
    2. Интерфейс pppN в состоянии UP
    """
    try:
        # Проверка 1: Процесс pppd существует
        try:
            result = subprocess.run(
                ['pgrep', '-f', f'pppd.*{node_id}'],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                logger.warning(f"⚠️ Node {node_id}: pppd процесс не найден")
                return False
        except Exception as e:
            logger.error(f"❌ Node {node_id}: Ошибка проверки pppd: {e}")
            return False
        
        # Проверка 2: Интерфейс UP
        try:
            result = subprocess.run(
                ['ip', 'link', 'show', ppp_interface],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.warning(f"⚠️ Node {node_id}: Интерфейс {ppp_interface} не существует")
                return False
            
            if 'state UP' not in result.stdout:
                logger.warning(f"⚠️ Node {node_id}: Интерфейс {ppp_interface} не в состоянии UP")
                return False
                
        except Exception as e:
            logger.error(f"❌ Node {node_id}: Ошибка проверки интерфейса: {e}")
            return False
        
        # Всё ОК
        return True
        
    except Exception as e:
        logger.error(f"❌ Node {node_id}: Критическая ошибка проверки PPTP: {e}")
        return False


def check_node_with_retries(node_id: int, ppp_interface: str) -> bool:
    """
    Проверить узел с гистерезисом (несколько попыток перед FAIL)
    """
    for attempt in range(1, WATCHDOG_PPTP_RETRIES + 1):
        logger.debug(f"🔍 Node {node_id}: Проверка PPTP (попытка {attempt}/{WATCHDOG_PPTP_RETRIES})")
        
        if check_pptp_tunnel(node_id, ppp_interface):
            logger.debug(f"✅ Node {node_id}: PPTP туннель здоров")
            return True
        
        # Если не последняя попытка - подождать
        if attempt < WATCHDOG_PPTP_RETRIES:
            logger.debug(f"⏳ Node {node_id}: Ожидание {WATCHDOG_RETRY_DELAY} сек перед следующей попыткой...")
            time.sleep(WATCHDOG_RETRY_DELAY)
    
    # Все попытки исчерпаны
    logger.error(f"❌ Node {node_id}: PPTP туннель не работает после {WATCHDOG_PPTP_RETRIES} попыток")
    return False


def watchdog_loop():
    """
    Основной цикл watchdog
    Проверяет все узлы со статусом 'online' каждые N секунд
    """
    logger.info(f"🔄 PPTP Watchdog запущен (интервал: {WATCHDOG_CHECK_INTERVAL} сек, retry: {WATCHDOG_PPTP_RETRIES})")
    
    while True:
        try:
            db = SessionLocal()
            
            # Импортируем модель Node
            from database import Node
            
            # Получить все online узлы
            online_nodes = db.query(Node).filter(Node.status == 'online').all()
            
            if not online_nodes:
                logger.debug("ℹ️ Нет online узлов для проверки")
            else:
                logger.info(f"🔍 Проверка {len(online_nodes)} online узлов...")
                
                for node in online_nodes:
                    if not node.ppp_interface:
                        logger.warning(f"⚠️ Node {node.id}: Нет ppp_interface, пропускаем")
                        continue
                    
                    # Проверка с гистерезисом
                    pptp_healthy = check_node_with_retries(node.id, node.ppp_interface)
                    
                    if not pptp_healthy:
                        # PPTP туннель упал -> переводим в FAIL
                        logger.error(f"💥 Node {node.id}: PPTP туннель упал, переводим в ping_failed")
                        
                        # Очистить SOCKS данные
                        node.status = 'ping_failed'
                        node.socks_ip = None
                        node.socks_port = None
                        node.socks_login = None
                        node.socks_password = None
                        node.ppp_interface = None
                        node.last_update = datetime.utcnow()
                        
                        # Остановить SOCKS сервис
                        try:
                            from socks_server import stop_socks_service
                            stop_socks_service(node.id)
                            logger.info(f"🛑 Node {node.id}: SOCKS сервис остановлен")
                        except Exception as e:
                            logger.error(f"❌ Node {node.id}: Ошибка остановки SOCKS: {e}")
                        
                        # Удалить PPTP туннель
                        try:
                            from pptp_tunnel_manager import pptp_tunnel_manager
                            pptp_tunnel_manager.destroy_tunnel(node.id)
                            logger.info(f"🗑️ Node {node.id}: PPTP туннель удален")
                        except Exception as e:
                            logger.error(f"❌ Node {node.id}: Ошибка удаления туннеля: {e}")
                    else:
                        logger.debug(f"✅ Node {node.id}: PPTP туннель здоров, SOCKS считается рабочим")
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Ошибка в watchdog loop: {e}")
            try:
                db.close()
            except:
                pass
        
        # Ожидание перед следующей проверкой
        logger.debug(f"⏳ Следующая проверка через {WATCHDOG_CHECK_INTERVAL} секунд...")
        time.sleep(WATCHDOG_CHECK_INTERVAL)


if __name__ == "__main__":
    logger.info("🚀 Запуск PPTP Watchdog...")
    try:
        watchdog_loop()
    except KeyboardInterrupt:
        logger.info("⛔ PPTP Watchdog остановлен (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 PPTP Watchdog критическая ошибка: {e}")
        sys.exit(1)
