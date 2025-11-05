#!/bin/bash
# ПОЛНАЯ РЕАЛИЗАЦИЯ РЕКОМЕНДАЦИЙ ChatGPT

echo "════════════════════════════════════════════════════════════════"
echo "  ПРИМЕНЕНИЕ ВСЕХ РЕКОМЕНДАЦИЙ ChatGPT"
echo "════════════════════════════════════════════════════════════════"

# 1. Системные настройки
echo "1. Системные настройки..."
sysctl -w net.ipv4.ip_forward=1 >/dev/null
sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null
for i in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 0 > $i 2>/dev/null; done

# 2. Firewall
echo "2. Firewall PPTP..."
iptables -C INPUT -p tcp --dport 1723 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 1723 -j ACCEPT
iptables -C INPUT -p gre -j ACCEPT 2>/dev/null || iptables -A INPUT -p gre -j ACCEPT

# 3. ip-up скрипт
echo "3. ip-up hook..."
cat > /etc/ppp/ip-up.d/20-connexa << 'EOFUP'
#!/bin/bash
DB="/app/backend/connexa.db"
NODE_ID="$IPPARAM"
IFACE="$IFNAME"
if [ -n "$NODE_ID" ] && [ -n "$IFACE" ]; then
 sqlite3 "$DB" "UPDATE nodes SET ppp_interface='$IFACE', status='online' WHERE id='$NODE_ID';"
fi
EOFUP
chmod +x /etc/ppp/ip-up.d/20-connexa

# 4. ip-down скрипт
echo "4. ip-down hook..."
cat > /etc/ppp/ip-down.d/20-connexa << 'EOFDOWN'
#!/bin/bash
DB="/app/backend/connexa.db"
NODE_ID="$IPPARAM"
if [ -n "$NODE_ID" ]; then
 sqlite3 "$DB" "UPDATE nodes SET ppp_interface=NULL, status='ping_ok' WHERE id='$NODE_ID';"
fi
EOFDOWN
chmod +x /etc/ppp/ip-down.d/20-connexa

# 5. Policy routing скрипт
echo "5. Policy routing helper..."
cat > /usr/local/bin/link_socks_to_ppp.sh << 'EOFLINK'
#!/bin/bash
PORT=$1;PPP=$2;MARK=$((PORT-1080));TABLE=$((100+MARK))
iptables -C INPUT -p tcp --dport $PORT -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport $PORT -j ACCEPT
iptables -t mangle -C PREROUTING -p tcp --dport $PORT -j MARK --set-mark $MARK 2>/dev/null || iptables -t mangle -A PREROUTING -p tcp --dport $PORT -j MARK --set-mark $MARK
ip rule show | grep -q "fwmark $MARK " || ip rule add fwmark $MARK table $TABLE
ip route replace default dev $PPP table $TABLE
sysctl -w net.ipv4.conf.$PPP.rp_filter=0 >/dev/null
echo "Routing: port $PORT -> $PPP (table $TABLE)"
EOFLINK
chmod +x /usr/local/bin/link_socks_to_ppp.sh

# 6. Очистка старых правил
echo "6. Очистка старых правил..."
for i in {100..200}; do ip rule del table $i 2>/dev/null; done
iptables -t mangle -F PREROUTING 2>/dev/null

echo "✅ ВСЕ РЕКОМЕНДАЦИИ ChatGPT ПРИМЕНЕНЫ!"
echo "Теперь: killall pppd && supervisorctl restart backend && Start Services"
