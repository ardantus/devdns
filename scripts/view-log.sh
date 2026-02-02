#!/usr/bin/env bash
# Tampilkan log query DNS. Bisa filter: semua / blocked / allowed.
# Pakai: ./scripts/view-log.sh [all|blocked|allowed] [-f]
#   all     = semua request (default)
#   blocked = hanya yang domain-nya ada di block list
#   allowed = hanya yang tidak di block list
#   -f      = follow (tail -f), tampil request baru terus

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="${REPO_ROOT}/logs/queries.log"
BLOCKED_CONF="${REPO_ROOT}/conf.d/blocked.conf"

MODE="${1:-all}"
FOLLOW=""
[[ "${2:-}" == "-f" ]] && FOLLOW="-f"
[[ "${1:-}" == "-f" ]] && FOLLOW="-f" && MODE="all"
[[ "${2:-}" == "-f" ]] && FOLLOW="-f"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "Log belum ada: $LOG_FILE" >&2
  echo "Pastikan container jalan (docker compose up -d) dan ada query DNS." >&2
  exit 1
fi

# Ambil daftar domain yang di-block (address=/domain/0.0.0.0)
blocked_domains() {
  grep -oE 'address=/[^/]+/0\.0\.0\.0' "$BLOCKED_CONF" 2>/dev/null | sed 's|address=/||;s|/0.0.0.0||' || true
}

# dnsmasq log format: [timestamp] query[TYPE] domain from IP
# Kita ekstrak "domain" dari baris yang berisi "query[" dan " from "
extract_domain() {
  sed -n 's/.*query\[[^]]*\] \([^ ]*\) from.*/\1/p'
}

# Cek apakah domain ada di block list (exact atau subdomain)
is_blocked() {
  local q="$1"
  while read -r b; do
    [[ -z "$b" ]] && continue
    [[ "$q" == "$b" ]] && return 0
    [[ "$q" == *".$b" ]] && return 0
  done < <(blocked_domains)
  return 1
}

filter_log() {
  case "$MODE" in
    all)
      if [[ -n "$FOLLOW" ]]; then tail -f "$LOG_FILE"; else cat "$LOG_FILE"; fi
      ;;
    blocked)
      if [[ -n "$FOLLOW" ]]; then
        tail -f "$LOG_FILE" | while read -r line; do
          domain=$(echo "$line" | extract_domain)
          if [[ -n "$domain" ]] && is_blocked "$domain"; then
            echo "[BLOCKED] $line"
          fi
        done
      else
        while read -r line; do
          domain=$(echo "$line" | extract_domain)
          if [[ -n "$domain" ]] && is_blocked "$domain"; then
            echo "[BLOCKED] $line"
          fi
        done < "$LOG_FILE"
      fi
      ;;
    allowed)
      if [[ -n "$FOLLOW" ]]; then
        tail -f "$LOG_FILE" | while read -r line; do
          domain=$(echo "$line" | extract_domain)
          if [[ -z "$domain" ]] || ! is_blocked "$domain"; then
            echo "[ALLOWED] $line"
          fi
        done
      else
        while read -r line; do
          domain=$(echo "$line" | extract_domain)
          if [[ -z "$domain" ]] || ! is_blocked "$domain"; then
            echo "[ALLOWED] $line"
          fi
        done < "$LOG_FILE"
      fi
      ;;
    *)
      echo "Mode: all | blocked | allowed" >&2
      echo "Pakai: $0 [all|blocked|allowed] [-f]" >&2
      exit 1
      ;;
  esac
}

filter_log
