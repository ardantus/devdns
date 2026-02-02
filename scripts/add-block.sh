#!/usr/bin/env bash
# Tambah domain ke daftar block (conf.d/blocked.conf).
# Pakai: ./scripts/add-block.sh domain.com
# Lalu: docker compose restart

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BLOCKED_CONF="$REPO_ROOT/conf.d/blocked.conf"
DOMAIN="${1:-}"

if [[ -z "$DOMAIN" ]]; then
  echo "Pakai: $0 <domain>" >&2
  echo "Contoh: $0 ads.example.com" >&2
  exit 1
fi

# Normalisasi: hilangkan trailing dot/spaces
DOMAIN="${DOMAIN%.}"
DOMAIN="${DOMAIN// /}"

if [[ -z "$DOMAIN" ]]; then
  echo "Domain tidak valid." >&2
  exit 1
fi

# Cek sudah ada atau belum
if grep -q "address=/${DOMAIN}/0.0.0.0" "$BLOCKED_CONF" 2>/dev/null; then
  echo "Domain '$DOMAIN' sudah ada di block list."
  exit 0
fi

echo "address=/${DOMAIN}/0.0.0.0" >> "$BLOCKED_CONF"
echo "Ditambah: $DOMAIN -> 0.0.0.0 di $BLOCKED_CONF"
echo "Restart container agar berlaku: docker compose restart"
