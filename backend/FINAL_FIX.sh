#!/bin/bash
echo "=== ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ PPTP+SOCKS ==="
echo "1. Убиваю все старые pppd..."
killall -9 pppd 2>/dev/null
killall -9 pptp 2>/dev/null
sleep 2
echo "2. Удаляю все ppp интерфейсы..."
for i in {0..100}; do ip link delete ppp$i 2>/dev/null; done
echo "3. Очищаю configs..."
rm -f /etc/ppp/peers/pptp_node_*
rm -f /tmp/pptp_node_*.log
echo "4. Очищаю БД..."
cd /app/backend
python3 << 'EOFPY'
from database import SessionLocal, Node
db = SessionLocal()
for n in db.query(Node).all():
    n.socks_ip = n.socks_port = n.socks_login = n.socks_password = n.ppp_interface = None
    if n.status == 'online': n.status = 'ping_ok'
db.commit()
db.close()
EOFPY
echo "5. Перезапуск backend..."
supervisorctl restart backend
sleep 5
echo ""
echo "✅ ГОТОВО! Система очищена."
echo "Теперь Start Services в админке!"
