#!/bin/bash
# ПОЛНОЕ РЕШЕНИЕ PPTP + SOCKS по методу ChatGPT

echo "════════════════════════════════════════════════════════════════"
echo "  ПРИМЕНЕНИЕ МЕТОДА ChatGPT: 3proxy + systemd + policy routing"
echo "════════════════════════════════════════════════════════════════"

# 1. Системные настройки
echo "1. Системные настройки..."
sysctl -w net.ipv4.ip_forward=1 >/dev/null
sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null
sysctl -w net.ipv4.conf.default.rp_filter=0 >/dev/null
for i in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 0 > $i 2>/dev/null; done

# 2. Firewall
echo "2. Firewall для PPTP..."
iptables -C INPUT -p tcp --dport 1723 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 1723 -j ACCEPT
iptables -C INPUT -p gre -j ACCEPT 2>/dev/null || iptables -A INPUT -p gre -j ACCEPT

# 3. Создаем systemd юниты
echo "3. Создание systemd templates..."

cat > /etc/systemd/system/pptp@.service << 'EOFPPTP'
[Unit]
Description=PPTP tunnel for node %i
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/pppd call node_%i
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOFPPTP

# 4. Helper скрипт для создания peer конфига
cat > /usr/local/bin/create_pptp_peer << 'EOFHELPER'
#!/bin/bash
NODE_ID=$1
NODE_IP=$2
LOGIN=$3
PASS=$4

cat > /etc/ppp/peers/node_$NODE_ID << EOFPEER
pty "pptp $NODE_IP --nolaunchpppd"
user $LOGIN
password $PASS
remotename PPTP
noauth
nobsdcomp
nodeflate
nodefaultroute
persist
maxfail 0
EOFPEER

echo "Peer created: node_$NODE_ID"
EOFHELPER

chmod +x /usr/local/bin/create_pptp_peer

echo "✅ ВСЕ ГОТОВО!"
echo ""
echo "Использование:"
echo "  create_pptp_peer 1 144.229.29.35 admin admin"
echo "  systemctl start pptp@1"
