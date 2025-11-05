#!/bin/bash
# Connexa Fix Pack - комплексное исправление SOCKS-over-PPTP
# Основано на рекомендациях ChatGPT-5 и диагностике Emergent.SH
set -euo pipefail

DB="/app/connexa.db"
BACKEND_DIR="/app/backend"
TS=$(date +%Y%m%d_%H%M%S)
LOG="/root/connexa_fix_${TS}.log"
mkdir -p /root

log(){ echo "[$(date +%F' '%T)] $*" | tee -a "$LOG"; }

log "🚀 Starting Connexa Fix Pack..."

# ========================================
# 0) SWAP 2GB (для стабильности памяти)
# ========================================
if ! swapon --show | grep -q "^/swapfile"; then
  log "📦 Adding 2GB swap..."
  fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q "/swapfile" /etc/fstab || echo "/swapfile none swap sw 0 0" >> /etc/fstab
  log "✅ Swap added"
else
  log "✅ Swap already present"
fi

# ========================================
# 1) Миграция БД: добавить ppp_interface
# ========================================
if [ -f "$DB" ]; then
  if ! sqlite3 "$DB" "PRAGMA table_info(nodes);" | awk -F'|' '{print $2}' | grep -qx "ppp_interface"; then
    log "📊 Adding ppp_interface column to database..."
    sqlite3 "$DB" "ALTER TABLE nodes ADD COLUMN ppp_interface VARCHAR(20);"
    log "✅ Database migrated"
  else
    log "✅ Column ppp_interface already exists"
  fi
else
  log "⚠️  WARNING: Database not found at $DB"
fi

# ========================================
# 2) Создать надежный link_socks_to_ppp.sh
# ========================================
log "📝 Creating link_socks_to_ppp.sh..."
mkdir -p /usr/local/bin
cat >/usr/local/bin/link_socks_to_ppp.sh <<'LINKSCRIPT'
#!/bin/bash
# Связывает SOCKS порт с PPP интерфейсом через policy routing
# Usage: link_socks_to_ppp.sh <socks_port> <ppp_iface>
set -euo pipefail

PORT="${1:?SOCKS port required}"
PPP="${2:?PPP interface required}"
MARK=$((PORT-1080))
[ $MARK -lt 1 ] && MARK=1
TABLE=$((100+MARK))

echo "[link] Starting: port=$PORT ppp=$PPP mark=$MARK table=$TABLE"

# ========================================
# Ждем готовности PPP интерфейса
# ========================================
for i in {1..20}; do
  if ip a show "$PPP" 2>/dev/null | grep -q "inet "; then
    echo "[link] PPP $PPP is UP with IP"
    break
  fi
  echo "[link] Waiting for $PPP ($i/20)..."
  sleep 1
done

# Финальная проверка
if ! ip a show "$PPP" 2>/dev/null | grep -q "inet "; then
  echo "[link] ERROR: PPP $PPP not ready after 20s"
  exit 1
fi

# ========================================
# Отключить rp_filter для PPP интерфейса
# ========================================
echo 0 > /proc/sys/net/ipv4/conf/$PPP/rp_filter 2>/dev/null || true

# ========================================
# Создать ip rule для fwmark → table
# ========================================
if ! ip rule show | grep -q "fwmark 0x$(printf '%x' $MARK)"; then
  ip rule add fwmark $MARK table $TABLE priority $((32000+MARK))
  echo "[link] Added ip rule: fwmark $MARK → table $TABLE"
else
  echo "[link] IP rule already exists"
fi

# ========================================
# Создать default route в таблице через PPP
# ========================================
if ! ip route show table $TABLE 2>/dev/null | grep -q "^default"; then
  ip route add default dev "$PPP" table $TABLE
  echo "[link] Added route: default dev $PPP table $TABLE"
else
  echo "[link] Route already exists"
fi

# ========================================
# iptables PREROUTING: пометить пакеты на PORT
# ========================================
CHAIN="PREROUTING"
TABLE_IPT="mangle"

# Проверяем, есть ли уже правило
if ! iptables -t $TABLE_IPT -S $CHAIN | grep -q "dpt:$PORT.*MARK set"; then
  iptables -t $TABLE_IPT -A $CHAIN -p tcp --dport $PORT -j MARK --set-mark $MARK
  iptables -t $TABLE_IPT -A $CHAIN -m mark --mark $MARK -j CONNMARK --save-mark
  echo "[link] Added iptables PREROUTING rules"
else
  echo "[link] iptables PREROUTING rules already exist"
fi

# ========================================
# iptables OUTPUT: восстановить mark для исходящих
# ========================================
if ! iptables -t $TABLE_IPT -S OUTPUT | grep -q "connmark match 0x$(printf '%x' $MARK)"; then
  iptables -t $TABLE_IPT -A OUTPUT -m connmark --mark $MARK -j MARK --set-mark $MARK
  echo "[link] Added iptables OUTPUT rules"
else
  echo "[link] iptables OUTPUT rules already exist"
fi

echo "[link] ✅ Successfully linked port=$PORT to $PPP (mark=$MARK table=$TABLE)"
exit 0
LINKSCRIPT

chmod +x /usr/local/bin/link_socks_to_ppp.sh
log "✅ link_socks_to_ppp.sh created"

# ========================================
# 3) Создать Watchdog
# ========================================
log "🐕 Creating watchdog..."
cat > /usr/local/bin/connexa_watchdog.py <<'WATCHDOG'
#!/usr/bin/env python3
"""
Connexa SOCKS Watchdog
Автоматически проверяет работоспособность SOCKS прокси и перезапускает неработающие
"""
import os
import sqlite3
import subprocess
import time
import json
import logging
from datetime import datetime

# Настройки
DB = os.environ.get("CONNEXA_DB", "/app/connexa.db")
API = os.environ.get("CONNEXA_API", "http://localhost:8001")
SERVER_IP = "167.172.218.138"
BATCH = int(os.environ.get("CONNEXA_BATCH", "5"))
SLEEP = float(os.environ.get("CONNEXA_SLEEP", "30"))
RETRIES = int(os.environ.get("CONNEXA_RETRIES", "3"))

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("watchdog")

def run_cmd(cmd, timeout=10):
    """Выполнить shell команду"""
    try:
        result = subprocess.run(
            cmd, shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True, 
            timeout=timeout
        )
        return result
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return None

def get_online_nodes():
    """Получить список активных SOCKS нод из БД"""
    if not os.path.exists(DB):
        logger.error(f"Database not found: {DB}")
        return []
    
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("""
            SELECT id, socks_port, ppp_interface, socks_login, socks_password 
            FROM nodes 
            WHERE status='online' AND socks_port IS NOT NULL
        """)
        
        nodes = []
        for row in cur.fetchall():
            nodes.append({
                'id': row[0],
                'port': row[1],
                'ppp': row[2],
                'login': row[3],
                'password': row[4]
            })
        
        con.close()
        return nodes
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []

def check_socks_proxy(node):
    """Проверить работоспособность SOCKS прокси"""
    proxy = f"socks5h://{node['login']}:{node['password']}@127.0.0.1:{node['port']}"
    
    try:
        result = run_cmd(
            f'timeout 8 curl -s -x "{proxy}" https://ipinfo.io/json -m 6',
            timeout=10
        )
        
        if not result or result.returncode != 0:
            logger.warning(f"[Node {node['id']}] curl failed")
            return False, None
        
        data = json.loads(result.stdout or '{}')
        ip = data.get('ip')
        
        if not ip:
            logger.warning(f"[Node {node['id']}] No IP in response")
            return False, None
        
        if ip == SERVER_IP:
            logger.error(f"[Node {node['id']}] ❌ Wrong IP: {ip} (server IP)")
            return False, ip
        
        logger.info(f"[Node {node['id']}] ✅ OK: IP={ip}")
        return True, ip
        
    except Exception as e:
        logger.error(f"[Node {node['id']}] Exception: {e}")
        return False, None

def ensure_routing(node):
    """Убедиться, что routing настроен для ноды"""
    if not node.get('ppp'):
        logger.warning(f"[Node {node['id']}] No PPP interface")
        return False
    
    try:
        result = run_cmd(
            f"/usr/local/bin/link_socks_to_ppp.sh {node['port']} {node['ppp']}",
            timeout=15
        )
        return result and result.returncode == 0
    except Exception as e:
        logger.error(f"[Node {node['id']}] Routing setup failed: {e}")
        return False

def restart_node_socks(node):
    """Перезапустить SOCKS для ноды через stop/start"""
    try:
        logger.info(f"[Node {node['id']}] Restarting SOCKS...")
        
        # Stop
        run_cmd(f"pkill -f 'socks.*{node['port']}'", timeout=5)
        time.sleep(2)
        
        # Ensure routing
        ensure_routing(node)
        
        # TODO: Start через API или прямой вызов
        # Пока просто обновляем routing
        
        return True
    except Exception as e:
        logger.error(f"[Node {node['id']}] Restart failed: {e}")
        return False

def mark_node_failed(node, reason):
    """Пометить ноду как failed в БД"""
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("""
            UPDATE nodes 
            SET status='ping_failed', 
                socks_ip=NULL,
                socks_port=NULL,
                socks_login=NULL,
                socks_password=NULL,
                last_update=?
            WHERE id=?
        """, (datetime.utcnow().isoformat(), node['id']))
        con.commit()
        con.close()
        logger.error(f"[Node {node['id']}] 🚫 Marked as FAILED: {reason}")
    except Exception as e:
        logger.error(f"[Node {node['id']}] Failed to mark as failed: {e}")

def main():
    """Основной цикл watchdog"""
    logger.info("🐕 Connexa SOCKS Watchdog started")
    logger.info(f"Config: BATCH={BATCH}, SLEEP={SLEEP}s, RETRIES={RETRIES}")
    
    retry_counters = {}
    
    while True:
        try:
            nodes = get_online_nodes()
            logger.info(f"Checking {len(nodes)} online nodes...")
            
            # Обрабатываем батчами
            for i in range(0, len(nodes), BATCH):
                batch = nodes[i:i + BATCH]
                
                for node in batch:
                    try:
                        # Проверяем routing
                        ensure_routing(node)
                        
                        # Проверяем работоспособность
                        is_ok, detected_ip = check_socks_proxy(node)
                        
                        if is_ok:
                            # Сбросить счетчик при успехе
                            if node['id'] in retry_counters:
                                del retry_counters[node['id']]
                        else:
                            # Увеличить счетчик неудач
                            retry_counters[node['id']] = retry_counters.get(node['id'], 0) + 1
                            
                            if retry_counters[node['id']] >= RETRIES:
                                logger.error(f"[Node {node['id']}] Max retries reached")
                                mark_node_failed(node, 'healthcheck_failed')
                                del retry_counters[node['id']]
                            else:
                                logger.warning(f"[Node {node['id']}] Retry {retry_counters[node['id']]}/{RETRIES}")
                                restart_node_socks(node)
                    
                    except Exception as e:
                        logger.error(f"[Node {node['id']}] Error: {e}")
                        mark_node_failed(node, f'watchdog_exception: {e}')
                
                # Пауза между батчами
                if i + BATCH < len(nodes):
                    time.sleep(3)
            
        except Exception as e:
            logger.error(f"Watchdog loop error: {e}")
        
        logger.info(f"Sleeping {SLEEP}s...")
        time.sleep(SLEEP)

if __name__ == "__main__":
    main()
WATCHDOG

chmod +x /usr/local/bin/connexa_watchdog.py
log "✅ Watchdog created"

# ========================================
# 4) Добавить Watchdog в Supervisor
# ========================================
if [ -d /etc/supervisor/conf.d ]; then
  log "📋 Configuring Supervisor..."
  cat >/etc/supervisor/conf.d/connexa_watchdog.conf <<'SUPERVISOR'
[program:connexa_watchdog]
command=/usr/bin/python3 /usr/local/bin/connexa_watchdog.py
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/connexa_watchdog.err.log
stdout_logfile=/var/log/supervisor/connexa_watchdog.out.log
environment=CONNEXA_DB="/app/connexa.db",CONNEXA_API="http://localhost:8001",CONNEXA_BATCH="5",CONNEXA_SLEEP="30",CONNEXA_RETRIES="3"
user=root
SUPERVISOR

  supervisorctl reread 2>/dev/null || true
  supervisorctl update 2>/dev/null || true
  log "✅ Supervisor configured"
else
  log "⚠️  Supervisor not found, skipping"
fi

# ========================================
# 5) Применить routing ко всем активным нодам
# ========================================
if [ -f "$DB" ]; then
  log "🔗 Applying routing to existing online nodes..."
  
  mapfile -t NODES < <(sqlite3 "$DB" "SELECT id,socks_port,ppp_interface FROM nodes WHERE status='online' AND socks_port IS NOT NULL;" 2>/dev/null || true)
  
  for row in "${NODES[@]}"; do
    IFS='|' read -r id port ppp <<<"$row"
    if [ -n "$port" ] && [ -n "$ppp" ]; then
      log "  Linking node $id: port=$port ppp=$ppp"
      /usr/local/bin/link_socks_to_ppp.sh "$port" "$ppp" 2>&1 | tee -a "$LOG" || true
    fi
  done
  
  log "✅ Routing applied"
fi

# ========================================
# 6) Увеличить лимиты файлов
# ========================================
log "📈 Increasing file limits..."
ulimit -n 65535 2>/dev/null || true
if ! grep -q "nofile 65535" /etc/security/limits.conf; then
  echo "* soft nofile 65535" >> /etc/security/limits.conf
  echo "* hard nofile 65535" >> /etc/security/limits.conf
fi
log "✅ File limits increased"

# ========================================
# Финал
# ========================================
log ""
log "========================================="
log "✅ Connexa Fix Pack completed!"
log "========================================="
log ""
log "Next steps:"
log "1. Check watchdog: supervisorctl status connexa_watchdog"
log "2. View logs: tail -f /var/log/supervisor/connexa_watchdog.out.log"
log "3. Test SOCKS: curl --socks5 login:pass@127.0.0.1:PORT https://ipinfo.io/json"
log ""
log "Log saved to: $LOG"
