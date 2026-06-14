# 📚 MUARA DATA

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**MUARA DATA** adalah pustaka Python yang memudahkan Anda **terhubung ke berbagai jenis database (ex. ClickHouse dan PostgreSQL)**, menjalankan query dengan **retry otomatis**, serta **memasukkan data DataFrame ke database** dengan konversi tipe data otomatis.

---

## ⚡️ Fitur Utama

🔀 **Multi-Database Support**  
Mendukung koneksi ke **ClickHouse**, **PostgreSQL**, dan **MySQL** melalui satu antarmuka sederhana.

🔄 **Retry Mechanism Otomatis**  
Menangani gangguan koneksi dengan retry berulang tanpa menghentikan proses utama.

📥 **Insert Data Otomatis**  
Mendukung konversi tipe data (float, int, string, array, datetime) dan opsi truncate sebelum insert.

🛡️ **Secure SSH Tunneling**     
Mendukung koneksi aman ke database di jaringan privat melalui **SSH Tunnel** (Bastion Host) dengan autentikasi kata sandi maupun SSH key.

⚙️ **Konfigurasi Fleksibel**  
Semua koneksi dikelola melalui file terenkripsi, tanpa perlu hard-code credential di kode.

🔑 **Credential Manager**  
Kelola kredensial database dengan aman dan cepat langsung melalui terminal menggunakan Credential Manager.

---

## 🧩 Instalasi

### 1. Install Muara Data
```bash
pip install muaradata
```

### 2. Daftarkan Credential Database
Jalankan perintah ```muaradb``` melalui terminal atau command-line.

Saat pertama kali dijalankan, aplikasi akan otomatis membuat:

- File `users.enc` dengan akun admin default
- File `credentials.enc` dengan contoh credential
- File `tunnels.enc` dengan contoh tunnel
- File `.key` untuk masing-masing file terenkripsi

#### Login Awal

```text
Username : admin
Password : Admin123!
```
> ⚠️ Sangat disarankan untuk segera mengganti password admin default
> setelah login pertama.

---

## Quick Start
```python
from muaradata import fetch_data

df = fetch_data("SELECT 1", aim="iriis_ch")
```

---

## 🚀 Cara Penggunaan

### 🔹 Import Library
```python
from muaradata import fetch_data, exec_query, insert_data, generate_table
```

---

## 🛠️ Fungsionalitas Utama

### 1. Menjalankan Query (`fetch_data`)
Menjalankan perintah SQL dan mengembalikan hasil sebagai `pandas.DataFrame`.

```python
df = fetch_data(
    query="SELECT * FROM sandbox.test_insert",
    aim="iriis_ch",
    retry_delay=10,
    max_retries=20
)
```

**Parameter:**
| Nama | Tipe | Default | Deskripsi |
|------|------|----------|------------|
| `query` | `str` | — | Perintah SQL yang akan dijalankan |
| `aim` | `str` | — | Nama koneksi sesuai `credentials` |
| `engine` | — | `None` | Objek koneksi database (optional) |
| `retry_delay` | `int` | `10` | Waktu tunggu antar percobaan koneksi (detik) (optional) |
| `max_retries` | `int` | `20` | Jumlah maksimum percobaan koneksi ulang (optional) |

---

### 2. Menjalankan Query Eksekusi (`exec_query`)
Digunakan untuk query yang **tidak mengembalikan data**, seperti `INSERT`, `UPDATE`, atau `DELETE`.

```python
result = exec_query("DELETE FROM sandbox.test_insert WHERE id = 10", aim="iriis_pg")
print(result)  # "Query Executed Successfully"
```

---

### 3. Menyimpan Data ke Database (`insert_data`)
Fungsi insert_data digunakan untuk menyisipkan data dari sebuah DataFrame ke dalam database seperti ClickHouse atau PostgreSQL. Fungsi ini mendukung konversi tipe data secara otomatis berdasarkan definisi kolom yang diberikan melalui parameter kolom.

```python
insert_data(
    result=df,
    aim='database_prod',
    nama_table='site.test_insert',
    kolom=kolom,
    truncate=False
)
```

Contoh struktur parameter kolom:
```python
kolom = {
    'all': ['id', 'nama', 'alamat'],       # Daftar semua kolom yang akan disisipkan
    'float': [],                           # Kolom bertipe float
    'integer': ['id'],                     # Kolom bertipe integer
    'string': ['nama', 'alamat'],          # Kolom bertipe string
    'array': ['combination_band'],         # Kolom bertipe array
    'datetime': []                         # Kolom bertipe datetime
}

```
> Jika tidak ada kolom untuk tipe tertentu, daftar dapat dikosongkan. Struktur ini memungkinkan konversi tipe data yang konsisten sebelum data dimasukkan ke dalam tabel database.

**Parameter:**
| Nama | Tipe | Deskripsi |
|------|------|------------|
| `result` | `DataFrame` | Data yang akan disimpan |
| `nama_table` | `str` | Nama tabel |
| `aim`	| `str`	| Nama koneksi database	|
| `kolom` | `dict` | Struktur kolom dan tipe datanya, tulis `auto` akan menyesuaikan dengan struktur dataframe |
| `truncate` | `bool` | Jika `True`, tabel akan dikosongkan sebelum insert (optional) |

**💡 Tips:**
> - Parameter `nama_table` harus diisi dengan nama tabel lengkap beserta schema-nya (misalnya: `schema.nama_tabel`).
> - Jika kedua parameter diisi, maka proses akan dilakukan pada kedua database secara bersamaan **dengan syarat** struktur tabel pada kedua database **identik**.
> - Jika struktur tabel berbeda, maka pemanggilan fungsi harus dilakukan secara terpisah untuk masing-masing database.
  
```python
# Contoh pemanggilan fungsi secara terpisah

kolom_tabel1 = {
    'all': [],
    'float': [],
    'integer': [],
    'string': [],
    'datetime': []
}
insert_data(
    result=df,
    aim='database_dev',
    nama_table='sandbox.test_insert',
    kolom=kolom_tabel,
    truncate=False
)

kolom_tabel2 = {
    'all': [],
    'float': [],
    'integer': [],
    'string': [],
    'datetime': []
}
insert_data(
    result=df,
    aim='database_prod',
    nama_table='site.test_insert',
    kolom=kolom_tabel2,
    truncate=True
)
```

---

### 4. Membuat Table (`generate_table`)

Fungsi `generate_table` digunakan untuk membuat perintah DDL (Data Definition Language) secara otomatis berdasarkan struktur dan tipe data yang terdapat dalam objek `pandas.DataFrame`. Perintah DDL yang dihasilkan akan disesuaikan dengan format tipe data yang sesuai untuk masing-masing database, dan kemudian dijalankan untuk membuat tabel secara langsung.

> Catatan: Pastikan struktur `DataFrame` telah sesuai dengan kebutuhan skema tabel sebelum menjalankan fungsi ini


**Parameter:**
| Nama | Tipe | Default | Deskripsi |
|------|------|----------|------------|
| `df` | `DataFrame` | - | Data yang akan dibuatkan tabel dan disimpan |
| `aim` | `str` | - | Nama koneksi database |
| `nama_table` | `str` | - | Nama tabel yang akan dibuat |
| `drop_table` | `str` | `True` | Menghapus table jika sudah ada didalam database |
| `ingest_data` | `bool` | `True` | Proses pengisian data ke dalam tabel setelah pembuatan |
| `**kwargs` | `str` | - | Parameter tambahan yang diteruskan ke generator.generate() untuk kedua driver (misal engine, order_by untuk ClickHouse MergeTree; schema, dtype untuk PostgreSQL). |

```
Returns:
    True jika proses selesai tanpa error.
```
Contoh Penggunaan:

```python
generate_table(
    df, 
    aim='database_prod',
    nama_table='default.sample_table',
    ingest_data=True
)
```
### Informasi Tambahan

- **Parameter `ingest_data`**  
  Isi `ingest_data = False` jika tidak ingin langsung melakukan proses pengisian data ke dalam tabel setelah pembuatan.
---

### 4. Mirroring Table (`copy_table`)

Menyalin struktur tabel dari satu server ke server lain, lintas platform dan lintas database (PostgreSQL ↔ ClickHouse atau driver apapun yang terdaftar di REGISTRY).   

Cara kerja:
>   1. Ambil sample baris dari tabel source untuk membaca struktur kolom dan tipe data (bukan full data, kecuali with_data=True).
>    2. Resolve driver destination dari kredensial aim_destination.
>    3. Buat tabel di destination via generate_table() dengan kolom yang
        sudah dinormalisasi. Ingest data hanya jika with_data=True.
```
Args:
    nama_table_source:      Nama tabel di server source, termasuk schema
                            jika diperlukan. Contoh: "public.tx_ticket".
    aim_source:             Alias koneksi source yang terdaftar di credentials.
                            Contoh: "iriis_pg", "iriis_ch".
    nama_table_destination: Nama tabel yang akan dibuat di server destination.
                            Contoh: "staging_area.tx_ticket".
    aim_destination:        Alias koneksi destination.
                            Contoh: "iriis_ch", "iriis_pg".
    drop_table:             Jika True, tabel destination di-drop & dibuat ulang
                            jika sudah ada. Default: True.
    with_data:              Jika True, data sample juga ikut dimasukkan ke
                            tabel destination setelah struktur dibuat.
                            Jika False, hanya struktur yang disalin. Default: False.
    sample_rows:            Jumlah baris yang diambil dari source untuk membaca
                            struktur. Nilai lebih besar membantu deteksi tipe kolom
                            yang lebih akurat (misal kolom dengan banyak NULL).
                            Default: 100.
    **kwargs:               Parameter tambahan yang diteruskan ke generate_table()
                            (misal engine, order_by untuk ClickHouse MergeTree).
```
```
Returns:
    True jika proses selesai tanpa error.
```
```
Raises:
    ValueError: Jika driver destination tidak dikenali atau tidak didukung.
    Exception:  Meneruskan exception dari fetch_data / generate_table.  
```    
Contoh penggunaan:
```
    from muaradata import copy_table
    
    # Salin struktur saja, dari PostgreSQL ke ClickHouse
    copy_table("public.tx_ticket", "db_source", "staging_area.tx_ticket", "db_staging")
    
    # Salin struktur + data sample, dari ClickHouse ke PostgreSQL
    copy_table(
        "staging_area.tx_ticket", "db_source",
        "public.tx_ticket", "db_staging",
        with_data=True,
        sample_rows=500,
    )
    
    # Salin antar ClickHouse dengan opsi engine khusus
    copy_table(
        "db_a.tx_ticket", "ch_server_a",
        "db_b.tx_ticket", "ch_server_b",
        engine="MergeTree()",
        order_by="id",
    )
```
---

## 🧾 Lisensi & Informasi

**Author    :** Redian Barqy Muhammad  
**Email :** rbm.eki@gmail.com    
**Copyright :** © 2025 MuaraData Project  


MIT License