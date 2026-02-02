#!/bin/sh
# Jalankan dnsmasq dengan log ke stderr, lalu tambah timestamp dan tulis ke file
# agar GoAccess bisa parse (butuh date/time).
set -e
mkdir -p /var/log/dnsmasq
dnsmasq -k 2>&1 | while read -r line; do
  echo "$(date '+%d/%b/%Y:%H:%M:%S') $line"
done >> /var/log/dnsmasq/queries.log
