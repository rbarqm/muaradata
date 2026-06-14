# 🗄️ IRIIS — Credential Manager CLI

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-internal--tool-orange)
![Security](https://img.shields.io/badge/storage-AES--128%20encrypted-red)

Alat berbasis **Command Line Interface (CLI)** yang ringan untuk mengelola
**credential database** dan **konfigurasi SSH tunnel** dengan dukungan
**autentikasi pengguna** serta **role-based access control**.

Seluruh data disimpan dalam file terenkripsi menggunakan format `.enc`
(Fernet Encryption), sehingga credential tidak pernah disimpan dalam bentuk plaintext di disk.

---

## Gambaran Umum

`app.py` merupakan entry point utama yang menyediakan antarmuka CLI interaktif
untuk beberapa fitur berikut:

- **Authentication** — proses login/logout menggunakan password yang di-hash (SHA-256)
- **User Management** — pengelolaan multi-user dengan role `admin` dan `user`
- **Credential Management** — penyimpanan dan pengelolaan koneksi database
- **Tunnel Management** — penyimpanan konfigurasi SSH tunnel
- **Role-Based Access Control** — pembatasan hak akses berdasarkan role pengguna

---

## Struktur Project

```text
project/
│
├── app.py                  ← entry point utama
├── cripter.py              ← modul enkripsi dan dekripsi
│
├── users.enc               ← data user (dibuat otomatis)
├── credentials.enc         ← data credential (dibuat otomatis)
├── tunnels.enc             ← data tunnel (dibuat otomatis)
│
├── kunci_users.key         ┐
├── kunci_creds.key         ├─ master key enkripsi (TIDAK di-commit)
├── kunci_tunnel.key        ┘
│
└── README.md
```

> ⚠️ Tambahkan seluruh file `.key` ke `.gitignore`
> agar tidak ikut ter-commit ke repository.

---

## Mekanisme Enkripsi

Proses enkripsi dikelola oleh modul `cripter.py`
menggunakan library `cryptography`
(Fernet / AES-128-CBC + HMAC-SHA256).

### Alur Enkripsi

```text
DataFrame → CSV bytes → Fernet.encrypt() → file .enc
```

### Alur Dekripsi

```text
file .enc → Fernet.decrypt() → CSV bytes → DataFrame
```

Master key akan di-load dengan urutan prioritas berikut:

1. Environment variable `CREDS_MASTER_KEY` *(direkomendasikan untuk production)*
2. File `.key` pada direktori project

Jika key tidak ditemukan, aplikasi akan menghasilkan `RuntimeError`.

---

## Instalasi

Pastikan Python versi **3.7 atau lebih baru** sudah terinstall.

Install dependency:

```bash
pip install pandas numpy tabulate cryptography
```

---

## Cara Menjalankan

Jalankan aplikasi menggunakan:

```bash
python app.py
```

atau jalankan:

```bash
iriisdb
```
Setelah install package `iriis_connection_library`

---

Saat pertama kali dijalankan, aplikasi akan otomatis membuat:

- File `users.enc` dengan akun admin default
- File `credentials.enc` dengan contoh credential
- File `tunnels.enc` dengan contoh tunnel
- File `.key` untuk masing-masing file terenkripsi

> ⚠️ Sangat disarankan untuk segera mengganti password admin default
> setelah login pertama.

---

## Login Awal

```text
Username : admin
Password : Admin123!
```

---

## Struktur Menu

### Sebelum Login (Guest)

```text
[1] Login
[0] Keluar
```

### Setelah Login — Role `user`

```text
── Profil ─────────────────────────
[1] Update profil saya
[2] Logout

── Credentials ─────────────────────
[7] Lihat credentials
[8] Tambah credential
[9] Edit credential
[10] Hapus credential

── Tunnels ─────────────────────────
[11] Lihat tunnels
[12] Tambah tunnel
[13] Edit tunnel
[14] Hapus tunnel

[0] Keluar
```

### Setelah Login — Role `admin`

Role `admin` memiliki seluruh menu milik `user`
ditambah fitur manajemen user berikut:

```text
── User Management (admin) ─────────
[3] Tambah user
[4] Lihat semua user
[5] Edit user
[6] Hapus user
```

---

## Role-Based Access Control

| Aksi | admin | user |
|---|:---:|:---:|
| Login / Logout | ✅ | ✅ |
| Update profil sendiri | ✅ | ✅ |
| Lihat semua user | ✅ | ❌ |
| Tambah / edit / hapus user lain | ✅ | ❌ |
| Mengubah role & status user | ✅ | ❌ |
| Lihat semua credential | ✅ | ✅ |
| Password credential tampil plaintext | ✅ | ❌ (`●●●●●●●●`) |
| Tambah credential | ✅ | ✅ |
| Edit / hapus credential milik sendiri | ✅ | ✅ |
| Edit / hapus credential milik user lain | ✅ | ❌ |
| Lihat semua tunnel | ✅ | ✅ |
| Password tunnel tampil plaintext | ✅ | ❌ (`●●●●●●●●`) |
| Tambah tunnel | ✅ | ✅ |
| Edit / hapus tunnel milik sendiri | ✅ | ✅ |
| Edit / hapus tunnel milik user lain | ✅ | ❌ |

> Field `owner` pada credential dan tunnel
> menyimpan username pembuat data.
>
> Seluruh user dapat melihat data,
> tetapi hanya pemilik data atau admin
> yang dapat mengedit maupun menghapusnya.

---

## Detail Fitur

### Authentication

Fitur autentikasi memiliki karakteristik berikut:

- Password disimpan dalam bentuk hash SHA-256
- Input password menggunakan `getpass`
  sehingga tidak tampil di terminal
- Status user (`active`) divalidasi saat login
- Session hanya disimpan di memori (in-memory)
  dan tidak pernah ditulis ke disk

---

### User Management *(Admin Only)*

Field data user:

| Field | Keterangan |
|---|---|
| `id` | Auto increment |
| `name` | Username unik |
| `password` | Hash SHA-256 |
| `first_name` | Nama depan |
| `last_name` | Nama belakang |
| `role` | `admin` atau `user` |
| `active` | `Y` (aktif) / `N` (nonaktif) |

Operasi yang tersedia:

- Menambah user baru dengan validasi username unik
- Password minimal 6 karakter
- Menampilkan seluruh user dalam bentuk tabel
- Mengedit role dan status user
- Menghapus user lain
- Admin tidak dapat menghapus akunnya sendiri

---

### Credential Management

Field credential yang disimpan:

| Field | Keterangan |
|---|---|
| `id` | Auto increment |
| `owner` | Username pembuat |
| `name` | Nama koneksi |
| `host` | Host/IP database |
| `port` | Port database |
| `username` | Username database |
| `password` | Password database |
| `database` | Nama database |
| `methode` | Nama library koneksi |
| `driver` | Nama driver/engine |
| `use_tunnel` | `True` / `False` |
| `name_tunnel` | Nama tunnel yang digunakan |

### Driver yang Didukung

| Pilihan | Methode | Driver |
|---|---|---|
| 1 | `clickhouse_driver` | `clickhouse` |
| 2 | `psycopg2` | `postgresql` |
| 3 | `clickhouse_connect` | `clickhouse` |
| 4 | `mysql` | `mysql` |

### Operasi Credential

- Menambah credential baru
- Mendukung wizard tunnel inline saat proses input
- Edit credential dengan mekanisme:
  field kosong = tidak diubah
- Menghapus credential dengan konfirmasi
- Seluruh user dapat melihat credential
- Password disembunyikan untuk non-admin

---

### Tunnel Management

Field tunnel yang disimpan:

| Field | Keterangan |
|---|---|
| `id` | Auto increment |
| `owner` | Username pembuat |
| `name` | Nama tunnel |
| `host_tunnel` | Host SSH |
| `user_tunnel` | Username SSH |
| `pass_tunnel` | Password SSH |

### Operasi Tunnel

- Menambah tunnel baru
- Dapat dipanggil langsung atau melalui wizard credential
- Jika nama tunnel diubah,
  seluruh referensi credential akan ikut diperbarui otomatis
- Jika tunnel dihapus,
  credential yang menggunakan tunnel tersebut
  akan otomatis dilepas:
  `use_tunnel=False`
  dan `name_tunnel=None`
- Password tunnel disembunyikan untuk non-admin

---

## Alur Sistem

```text
app.py
│
├── init()               ← cek & buat file .enc jika belum ada
│
├── main() [while loop]
│   ├── Guest → login()
│   └── Logged in
│       ├── user_*()     ← manajemen user
│       ├── cred_*()     ← CRUD credential
│       └── tunnel_*()   ← CRUD tunnel
│
└── cripter.py
    ├── generate_key()   ← generate master key
    ├── load_key()       ← load key dari env/file
    ├── encrypt_csv()    ← DataFrame → .enc
    └── decrypt_csv()    ← .enc → DataFrame
```

---

## Manajemen Key

### Environment Development

Key disimpan sebagai file `.key`
di direktori project:

```bash
kunci_users.key
kunci_creds.key
kunci_tunnel.key
```

> File `.key` dibuat otomatis saat pertama kali aplikasi dijalankan.
> Jangan menyimpan file ini ke repository Git.

---

### Environment Production

Untuk production,
disarankan menggunakan environment variable:

```bash
export CREDS_MASTER_KEY="your-base64-fernet-key-here"
```

Generate key baru:

```python
from cryptography.fernet import Fernet

print(Fernet.generate_key().decode())
```

> Key yang sama wajib digunakan pada seluruh environment
> agar file `.enc` tetap dapat dibaca.
>
> Jika key hilang, data tidak dapat direcover.

---

## Rekomendasi `.gitignore`

```gitignore
*.key
*.enc
```

---

## Dependency

| Library | Minimum Version | Fungsi |
|---|---|---|
| `pandas` | 1.3+ | Manipulasi data CSV |
| `numpy` | 1.21+ | Operasi data |
| `tabulate` | 0.8+ | Format tabel terminal |
| `cryptography` | 3.4+ | Enkripsi Fernet |
| `hashlib` | stdlib | Hash password SHA-256 |
| `getpass` | stdlib | Input password tersembunyi |

---

## Catatan Keamanan

| Aspek | Implementasi |
|---|---|
| Password user | SHA-256 hash |
| Credential & tunnel | Fernet encrypted |
| Input password | `getpass` |
| Master key | Environment variable / `.key` |
| Session | In-memory |
| Hak akses | Role-based & owner-based |

Untuk kebutuhan production dengan standar keamanan lebih tinggi,
disarankan menggunakan layanan secret management seperti:

- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault
- GCP Secret Manager

---

## Author & License

**Author:** Redian Barqy Muhammad

**Email:** redian.muhammad@sigma.co.id

**Copyright:** © 2025 IRIIS Project

MIT License
