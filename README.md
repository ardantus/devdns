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

## Cara pakai

1. Jalankan: `docker compose up -d`
2. Set DNS sistem (Wi‑Fi/Ethernet) ke `127.0.0.1`
3. Buka domain lokal di browser (misalnya `http://microumkm.test`)

Query ke domain lain (google.com, dll.) tetap diteruskan ke upstream DNS; internet tidak terganggu.
