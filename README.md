# devdns — Local Development

Repositori ini membantu **local development** dengan menyediakan **server DNS lokal** di Docker. Dengan ini Anda tidak perlu repot mengatur DNS sistem atau edit hosts manual—cukup definisikan domain lokal per proyek dan arahkan ke `127.0.0.1`.

## TLD yang disarankan untuk domain lokal

Gunakan TLD yang aman dan tidak bentrok dengan internet:

| TLD        | Keterangan                          | Keamanan   |
|-----------|--------------------------------------|------------|
| **`.test`**   | Reserved untuk testing (RFC 6761)   | Paling aman |
| **`.localhost`** | Reserved untuk localhost            | Aman       |
| **`.lan`**    | Umum dipakai untuk LAN              | Aman       |
| **`.example`** | Reserved untuk dokumentasi (RFC 6761) | Aman    |

Disarankan: pakai **`.test`** untuk project development (misalnya `microumkm.test`).

## Konfigurasi per domain

Satu file `.conf` per domain di folder **conf.d/**.

Contoh:

- `conf.d/microumkm.test.conf`
- `conf.d/proyek-lain.test.conf`

Contoh isi file untuk domain baru:

```
# Domain: namadomain.test
address=/namadomain.test/127.0.0.1
```

Setelah menambah atau mengubah file, restart container:

```bash
docker compose restart
```

## Log setiap request

Setiap query DNS dicatat ke **logs/queries.log**. Berguna untuk debug atau memantau lalu lintas DNS.

### Menampilkan log

| Cara | Perintah |
|------|----------|
| **Semua request** | `./scripts/view-log.sh` atau `tail -f logs/queries.log` |
| **Hanya yang di-BLOCK** | `./scripts/view-log.sh blocked` |
| **Hanya yang di-ALLOW** | `./scripts/view-log.sh allowed` |
| **Ikuti request baru (live)** | `./scripts/view-log.sh all -f` atau `./scripts/view-log.sh blocked -f` |

Contoh baris log query (baris lain seperti startup dnsmasq tidak dihitung):

```
02/Feb/2026:08:18:41 query[A] microumkm.test from 127.0.0.1
02/Feb/2026:08:18:42 query[AAAA] google.com from 127.0.0.1
```

Script **view-log** memisahkan **blocked** vs **allowed** dengan memeriksa daftar block di `conf.d/blocked.conf`.

## Web UI log viewer (port 8053)

Log query DNS bisa dilihat di **web UI** (tanpa GoAccess; cocok untuk log dnsmasq).

1. Jalankan semua service:  
   `docker compose up -d`
2. Buka di browser: **http://localhost:8053**

Tampilan: tabel query (waktu, tipe, domain, client, status Blocked/Allowed) dengan filter **Semua** / **Allowed** / **Blocked**. Refresh otomatis setiap 5 detik.

## Block list (domain yang diblokir)

Domain yang ingin diblokir (jawaban `0.0.0.0`) dikelola di **conf.d/blocked.conf**.

### Menambah domain ke block list

**Opsi 1 — script (disarankan):**

```bash
./scripts/add-block.sh ads.example.com
docker compose restart
```

**Opsi 2 — edit manual:**

Tambahkan baris di `conf.d/blocked.conf`:

```
address=/ads.example.com/0.0.0.0
```

Lalu restart:

```bash
docker compose restart
```

Setelah itu, query ke domain tersebut akan dijawab `0.0.0.0` dan muncul sebagai **blocked** di log viewer.

## Cara pakai

1. Jalankan: `docker compose up -d`
2. Set DNS sistem (Wi‑Fi/Ethernet) ke `127.0.0.1`
3. Buka domain lokal di browser (misalnya `http://microumkm.test`)

Query ke domain lain (google.com, dll.) tetap diteruskan ke upstream DNS; internet tidak terganggu.
