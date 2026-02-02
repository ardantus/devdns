#!/usr/bin/env python3
"""
Web UI log viewer untuk log DNS dnsmasq.
Port 8053. Tanpa dependency eksternal (stdlib only).
"""
import json
import os
import re
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

LOG_FILE = os.environ.get("LOG_FILE", "/var/log/dnsmasq/queries.log")
BLOCKED_CONF = os.environ.get("BLOCKED_CONF", "/etc/dnsmasq.d/blocked.conf")
PORT = int(os.environ.get("HTTP_PORT", "8053"))

# Baris log query: timestamp [dnsmasq[N]: ] query[TIPE] domain from IP
# Contoh: 02/Feb/2026:08:57:24 dnsmasq[8]: query[A] dns.google from 151.101.2.132
QUERY_RE = re.compile(
    r"^(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})\s+(?:dnsmasq\[\d+\]:\s+)?query\[([^\]]+)\]\s+([^\s]+)\s+from\s+(\S+)"
)


def read_blocked_domains():
    domains = set()
    if not os.path.isfile(BLOCKED_CONF):
        return domains
    with open(BLOCKED_CONF, "r") as f:
        for line in f:
            m = re.search(r"address=/([^/]+)/0\.0\.0\.0", line)
            if m:
                domains.add(m.group(1).strip())
    return domains


def is_domain_blocked(domain, blocked_set):
    if not blocked_set:
        return False
    for b in blocked_set:
        if domain == b or domain.endswith("." + b):
            return True
    return False


def parse_log(filter_mode="all"):
    blocked_set = read_blocked_domains()
    entries = []
    if not os.path.isfile(LOG_FILE):
        return entries
    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            m = QUERY_RE.search(line)
            if not m:
                continue
            ts, qtype, domain, client = m.groups()
            blocked = is_domain_blocked(domain, blocked_set)
            if filter_mode == "blocked" and not blocked:
                continue
            if filter_mode == "allowed" and blocked:
                continue
            entries.append(
                {
                    "time": ts,
                    "type": qtype,
                    "domain": domain,
                    "client": client,
                    "blocked": blocked,
                }
            )
    return list(reversed(entries))  # terbaru di atas


PER_PAGE = 20


HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>devdns – Log DNS</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; margin: 0; padding: 1rem; background: #0f1419; color: #e6edf3; }
    h1 { font-size: 1.25rem; margin-bottom: 0.5rem; }
    .meta { color: #8b949e; font-size: 0.875rem; margin-bottom: 1rem; }
    .filters { margin-bottom: 1rem; }
    .filters a { color: #58a6ff; margin-right: 1rem; text-decoration: none; }
    .filters a:hover { text-decoration: underline; }
    .filters a.active { font-weight: bold; }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #21262d; }
    th { color: #8b949e; font-weight: 600; }
    .blocked { color: #f85149; }
    .allowed { color: #3fb950; }
    .badge { display: inline-block; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.75rem; }
    .badge.blocked { background: rgba(248,81,73,.2); color: #f85149; }
    .badge.allowed { background: rgba(63,185,80,.2); color: #3fb950; }
    .empty { color: #8b949e; padding: 2rem; }
    .pagination { margin-top: 1rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; color: #8b949e; font-size: 0.875rem; }
    .pagination a, .pagination span { color: #58a6ff; text-decoration: none; padding: 0.25rem 0.5rem; border-radius: 4px; }
    .pagination a:hover { background: #21262d; }
    .pagination .current { font-weight: bold; color: #e6edf3; }
    .pagination .disabled { color: #484f58; pointer-events: none; }
    .realtime-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .realtime-row label { display: flex; align-items: center; gap: 0.35rem; cursor: pointer; color: #8b949e; font-size: 0.875rem; }
    .realtime-row input[type="checkbox"] { cursor: pointer; }
    .realtime-badge { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; background: rgba(63,185,80,.2); color: #3fb950; }
    .realtime-badge::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; animation: pulse 1s ease-in-out infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
  </style>
</head>
<body>
  <h1>devdns – Log DNS</h1>
  <p class="meta">Log query DNS dari dnsmasq. 20 baris per halaman.</p>
  <div class="realtime-row">
    <label><input type="checkbox" id="realtime-cb"> Realtime (refresh tiap 5 detik)</label>
    <span id="realtime-badge" class="realtime-badge" style="display:none">Realtime</span>
  </div>
  <div class="filters">
    <a href="/?filter=all&page=1" id="f-all">Semua</a>
    <a href="/?filter=allowed&page=1" id="f-allowed">Allowed</a>
    <a href="/?filter=blocked&page=1" id="f-blocked">Blocked</a>
  </div>
  <table>
    <thead>
      <tr><th>Waktu</th><th>Tipe</th><th>Domain</th><th>Client</th><th>Status</th></tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div id="pagination" class="pagination"></div>
  <script>
    const tbody = document.getElementById('tbody');
    const paginationEl = document.getElementById('pagination');
    const params = new URLSearchParams(location.search);
    let filter = params.get('filter') || 'all';
    let page = Math.max(1, parseInt(params.get('page') || '1', 10));
    document.querySelectorAll('.filters a').forEach(a => {
      const href = new URL(a.href);
      a.classList.toggle('active', (a.id === 'f-' + filter));
    });
    function buildPageUrl(p) {
      const u = new URL(location.href);
      u.searchParams.set('filter', filter);
      u.searchParams.set('page', String(p));
      return u.pathname + u.search;
    }
    function render(data) {
      const entries = data.entries || [];
      const total = data.total || 0;
      const totalPages = data.total_pages || 1;
      if (entries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty">Belum ada query DNS.</td></tr>';
      } else {
        tbody.innerHTML = entries.map(e => `
          <tr>
            <td>${e.time}</td>
            <td>${e.type}</td>
            <td>${e.domain}</td>
            <td>${e.client}</td>
            <td><span class="badge ${e.blocked ? 'blocked' : 'allowed'}">${e.blocked ? 'Blocked' : 'Allowed'}</span></td>
          </tr>
        `).join('');
      }
      if (totalPages <= 1) {
        paginationEl.innerHTML = total ? '<span>Baris 1–' + Math.min(20, total) + ' dari ' + total + '</span>' : '';
      } else {
        let html = '';
        if (page > 1) html += '<a href="' + buildPageUrl(1) + '">« Pertama</a><a href="' + buildPageUrl(page - 1) + '">‹ Prev</a>';
        else html += '<span class="disabled">« Pertama</span><span class="disabled">‹ Prev</span>';
        const start = Math.max(1, page - 2);
        const end = Math.min(totalPages, page + 2);
        for (let i = start; i <= end; i++) {
          if (i === page) html += '<span class="current">' + i + '</span>';
          else html += '<a href="' + buildPageUrl(i) + '">' + i + '</a>';
        }
        if (page < totalPages) html += '<a href="' + buildPageUrl(page + 1) + '">Next ›</a><a href="' + buildPageUrl(totalPages) + '">Terakhir »</a>';
        else html += '<span class="disabled">Next ›</span><span class="disabled">Terakhir »</span>';
        const from = (page - 1) * 20 + 1;
        const to = Math.min(page * 20, total);
        html += '<span style="margin-left:0.5rem">Baris ' + from + '–' + to + ' dari ' + total + '</span>';
        paginationEl.innerHTML = html;
      }
    }
    function fetchLog() {
      fetch('/api/log?filter=' + filter + '&page=' + page + '&per_page=20').then(r => r.json()).then(render).catch(() => {});
    }
    const realtimeCb = document.getElementById('realtime-cb');
    const realtimeBadge = document.getElementById('realtime-badge');
    let realtimeInterval = null;
    realtimeCb.checked = localStorage.getItem('devdns-realtime') === '1';
    if (realtimeCb.checked) {
      realtimeBadge.style.display = 'inline-flex';
      realtimeInterval = setInterval(fetchLog, 5000);
    }
    realtimeCb.addEventListener('change', function() {
      if (this.checked) {
        realtimeBadge.style.display = 'inline-flex';
        realtimeInterval = setInterval(fetchLog, 5000);
        localStorage.setItem('devdns-realtime', '1');
      } else {
        realtimeBadge.style.display = 'none';
        if (realtimeInterval) clearInterval(realtimeInterval);
        realtimeInterval = null;
        localStorage.setItem('devdns-realtime', '0');
      }
    });
    fetchLog();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        filter_mode = (query.get("filter") or ["all"])[0]
        if filter_mode not in ("all", "blocked", "allowed"):
            filter_mode = "all"

        if path == "/api/log":
            entries = parse_log(filter_mode)
            total = len(entries)
            page = max(1, int((query.get("page") or ["1"])[0]))
            per_page = max(1, min(100, int((query.get("per_page") or [str(PER_PAGE)])[0])))
            total_pages = max(1, (total + per_page - 1) // per_page)
            page = min(page, total_pages)
            start = (page - 1) * per_page
            slice_entries = entries[start : start + per_page]
            out = {
                "entries": slice_entries,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(out).encode())
            return

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Log viewer: http://0.0.0.0:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
