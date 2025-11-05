#!/bin/bash
# Полная диагностика SOCKS/PPTP по ТЗ ChatGPT
TS=$(date +%Y%m%d_%H%M%S)
OUT=/root/connexa_diag_$TS
mkdir -p "$OUT"

echo "════════════════════════════════════════════════════════════════"
echo "СБОР ДИАГНОСТИКИ SOCKS/PPTP - $TS"
echo "════════════════════════════════════════════════════════════════"

# 1. ПРОЦЕССЫ / РЕСУРСЫ / ЛИМИТЫ
echo "1. Процессы и ресурсы..."
{
  echo "=== FREE ==="
  free -h
  echo ""
  echo "=== MEMINFO ==="
  cat /proc/meminfo | egrep 'Mem|Swap' -n
  echo ""
  echo "=== ULIMIT ==="
  ulimit -n
  echo ""
  echo "=== SYSCTL ==="
  sysctl net.core.somaxconn fs.file-max
  echo ""
  echo "=== PROCESSES COUNT ==="
  ps aux | egrep 'uvicorn|pppd' | grep -v grep | wc -l
  echo ""
  echo "=== PROCESSES LIST ==="
  ps aux | egrep 'uvicorn|pppd' | grep -v grep | head -50
} > "$OUT/resources.txt" 2>&1

# 2. SUPERVISOR / ЛОГИ
echo "2. Supervisor и логи..."
{
  echo "=== SUPERVISOR STATUS ==="
  supervisorctl status
  echo ""
  echo "=== BACKEND ERR LOG (last 300) ==="
  tail -n 300 /var/log/supervisor/backend.err.log
  echo ""
  echo "=== BACKEND OUT LOG (last 200) ==="
  tail -n 200 /var/log/supervisor/backend.out.log 2>/dev/null || echo "No out log"
} > "$OUT/supervisor_logs.txt" 2>&1

# 3. POLICY ROUTING
echo "3. Policy routing..."
{
  echo "=== IP RULE ==="
  ip rule show
  echo ""
  echo "=== IPTABLES MANGLE ==="
  iptables -t mangle -L -v -n | egrep 'MARK|CONNMARK'
  echo ""
  echo "=== ONLINE УЗЛЫ ИЗ БД ==="
  sqlite3 /app/backend/connexa.db "SELECT id,socks_port,ppp_interface FROM nodes WHERE status='online';"
} > "$OUT/policy_routing.txt" 2>&1

# 4. ПРОВЕРКА КАЖДОГО УЗЛА
echo "4. Проверка каждого online узла..."
sqlite3 /app/backend/connexa.db "SELECT id,socks_port,ppp_interface,socks_login,socks_password FROM nodes WHERE status='online';" 2>/dev/null | while IFS='|' read id port ppp user pass; do
  mark=$((port-1080))
  table=$((100+mark))
  {
    echo "════════════════════════════════════════"
    echo "NODE $id  PORT $port  PPP $ppp  MARK $mark  TABLE $table"
    echo "════════════════════════════════════════"
    echo "--- PPP интерфейс:"
    ip a show "$ppp" 2>&1 | head -5 || echo "NO_PPP"
    echo ""
    echo "--- IP RULE:"
    ip rule | grep -E "fwmark.*$mark" || echo "NO_RULE"
    echo ""
    echo "--- ROUTING TABLE:"
    ip route show table $table 2>&1 || echo "NO_TABLE"
    echo ""
    echo "--- ТЕСТ SOCKS:"
    timeout 6 curl -s -x "socks5://$user:$pass@127.0.0.1:$port" https://ipinfo.io/json 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ IP:',d.get('ip'),'City:',d.get('city'))" 2>&1 || echo "❌ SOCKS_FAIL"
    echo ""
  } >> "$OUT/node_checks.txt"
done

# 5. DNS ТЕСТЫ
echo "5. DNS тесты..."
{
  echo "=== RESOLV CONF ==="
  resolvectl status 2>/dev/null || cat /etc/resolv.conf
  echo ""
  echo "=== DIG TEST ==="
  dig +time=2 +tries=1 whoer.net @1.1.1.1 2>&1 | head -20
  echo ""
  echo "=== CURL WITH RESOLVE ==="
  timeout 6 curl -s --resolve whoer.net:443:104.26.11.233 https://whoer.net/ -v 2>&1 | head -10
} > "$OUT/dns_tests.txt" 2>&1

# 6. БД + ВЕРСИИ
echo "6. БД и версии..."
{
  echo "=== DB SCHEMA ==="
  sqlite3 /app/backend/connexa.db ".schema nodes"
  echo ""
  echo "=== ONLINE NODES ==="
  sqlite3 /app/backend/connexa.db "SELECT id,status,socks_port,ppp_interface FROM nodes WHERE status='online';"
  echo ""
  echo "=== PIP VERSIONS ==="
  cd /app/backend && source venv/bin/activate && pip freeze | egrep 'uvicorn|fastapi|httpx|anyio'
} > "$OUT/db_versions.txt" 2>&1

# 7. LISTENING PORTS
echo "7. Listening ports..."
ss -lntp | grep -E ':(10(8|9)[0-9]|11[0-9]{2}) ' > "$OUT/listen_ports.txt" 2>&1

# 8. Создание архива
echo "8. Создание архива..."
cd /root
tar -czf "connexa_diag_$TS.tgz" "connexa_diag_$TS/" 2>&1

echo ""
echo "✅ ДИАГНОСТИКА ЗАВЕРШЕНА"
echo "📦 Архив: /root/connexa_diag_$TS.tgz"
echo ""
echo "Краткая сводка:"
cat "$OUT/node_checks.txt" | grep -E "NODE|✅|❌"
