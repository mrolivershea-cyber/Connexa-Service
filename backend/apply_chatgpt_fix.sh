#!/bin/bash
echo "ПРИМЕНЯЮ РЕКОМЕНДАЦИИ ChatGPT"
echo "1. ip-up скрипт..."
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
echo "2. ip-down скрипт..."
cat > /etc/ppp/ip-down.d/20-connexa << 'EOFDOWN'
#!/bin/bash
DB="/app/backend/connexa.db"
NODE_ID="$IPPARAM"
if [ -n "$NODE_ID" ]; then
 sqlite3 "$DB" "UPDATE nodes SET ppp_interface=NULL, status='ping_ok' WHERE id='$NODE_ID';"
fi
EOFDOWN
chmod +x /etc/ppp/ip-down.d/20-connexa
echo "3. link_socks_to_ppp скрипт..."
cat > /usr/local/bin/link_socks_to_ppp.sh << 'EOFLINK'
#!/bin/bash
PORT=$1
PPP=$2
MARK=$((PORT-1080))
TABLE=$((100+MARK))
iptables -t mangle -C PREROUTING -p tcp --dport $PORT -j MARK --set-mark $MARK 2>/dev/null || iptables -t mangle -A PREROUTING -p tcp --dport $PORT -j MARK --set-mark $MARK
ip rule show | grep -q "fwmark $MARK" || ip rule add fwmark $MARK table $TABLE
ip route replace default dev $PPP table $TABLE
sysctl -w net.ipv4.conf.$PPP.rp_filter=0 >/dev/null
echo "Routing: port $PORT -> $PPP (table $TABLE)"
EOFLINK
chmod +x /usr/local/bin/link_socks_to_ppp.sh
echo "✅ ГОТОВО!"
