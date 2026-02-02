#!/bin/sh
# Generate report, jalankan GoAccess daemon (WebSocket), lalu serve HTML di port 8053.
LOG_FILE="${LOG_FILE:-/var/log/dnsmasq/queries.log}"
CONFIG="${CONFIG:-/etc/goaccess/goaccess.conf}"
OUTPUT="${OUTPUT:-/var/www/html/index.html}"
WS_PORT="${WS_PORT:-7890}"
HTTP_PORT="${HTTP_PORT:-8053}"

mkdir -p /var/www/html
touch "$LOG_FILE"

# Jalankan GoAccess; jika gagal (mis. log kosong), buat placeholder supaya container tetap jalan
if ! goaccess "$LOG_FILE" \
  -o "$OUTPUT" \
  -p "$CONFIG" \
  --real-time-html \
  --ws-url="ws://localhost:${WS_PORT}" \
  --port="${WS_PORT}" \
  --addr=0.0.0.0 \
  --daemonize 2>/dev/null; then
  printf '%s\n' '<!DOCTYPE html><html><head><meta charset="utf-8"><title>devdns GoAccess</title></head>' \
    '<body><h1>GoAccess – devdns</h1><p>Menunggu data log DNS. Pastikan container devdns jalan dan ada query ke DNS.</p>' \
    '<p>Log: '"$LOG_FILE"'</p><p>Refresh halaman setelah ada request.</p></body></html>' > "$OUTPUT"
fi

# Pastikan file ada untuk httpd
[ -f "$OUTPUT" ] || echo '<html><body><h1>Report akan muncul setelah ada log.</h1></body></html>' > "$OUTPUT"

exec busybox httpd -f -p "$HTTP_PORT" -h /var/www/html
