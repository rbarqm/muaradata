import warnings
warnings.filterwarnings("ignore")

import os
import sys
import hashlib
import getpass
import numpy as np
import pandas as pd
from tabulate import tabulate

from .cripter import _key_path, generate_key, load_key, encrypt_csv, decrypt_csv

"""
    Unified CLI: Login + User Management + Credential & Tunnel Manager

    Aturan akses:
    - Admin : bisa lihat/kelola semua credential & tunnel, password tidak disembunyikan
    - User  : hanya bisa lihat/kelola credential & tunnel milik sendiri, password disembunyikan

    Author     : Redian Barqy Muhammad <rbm.eki@gmail.com>
    Copyright  : Copyright 2024, MuaraData Project
"""

# ══════════════════════════════════════════════════════════════
# PATH & KONSTANTA
# ══════════════════════════════════════════════════════════════
#
#  File .enc  → disimpan di direktori project (BASE_DIR), boleh di-commit
#               karena sudah terenkripsi.
#
#  File .key  → disimpan di system config dir OS, TIDAK di project:
#               Linux   : ~/.config/muaradata/
#               macOS   : ~/Library/Application Support/muaradata/
#               Windows : C:\Users\<user>\AppData\Local\muaradata\
#
#               Nama file di-hash dari seed internal sehingga tidak
#               mengandung kata "key", "kunci", atau nama engine apapun.
#               Contoh hasil: 0e8ebdd27d82.dat
#
# ══════════════════════════════════════════════════════════════

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))

USER_PATH    = os.path.join(BASE_DIR, 'users.enc')
CREDS_PATH   = os.path.join(BASE_DIR, 'credentials.enc')
TUNNELS_PATH = os.path.join(BASE_DIR, 'tunnels.enc')

KEY_USERS    = _key_path("muaradata_users_store")
KEY_CREDS    = _key_path("muaradata_creds_store")
KEY_TUNNS    = _key_path("muaradata_tunns_store")

COLS_USER   = ['id', 'name', 'password', 'first_name', 'last_name', 'role', 'active']
COLS_CREDS  = ['id', 'owner', 'name', 'host', 'port', 'username', 'password',
               'database', 'methode', 'driver', 'use_tunnel', 'name_tunnel']
COLS_TUNNEL = ['id', 'owner', 'name', 'host_tunnel', 'user_tunnel', 'pass_tunnel']

MAP_DRIVER = {
    '1': ['clickhouse_driver',  'clickhouse'],
    '2': ['psycopg2',           'postgresql'],
    '3': ['clickhouse_connect', 'clickhouse'],
    '4': ['mysql',              'mysql'],
}

SESSION: dict = {"user": None}


# ══════════════════════════════════════════════════════════════
# HELPER UMUM
# ══════════════════════════════════════════════════════════════

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def divider(title="", width=58):
    if title:
        pad = width - len(title) - 4
        print(f"\n─── {title} {'─' * max(pad, 2)}")
    else:
        print("─" * width)

def confirm(msg: str) -> bool:
    return input(f"{msg} (y/N): ").strip().lower() == 'y'

def input_pass(label="Password", hide=True) -> str:
    if hide:
        try:
            return getpass.getpass(f"{label}: ")
        except Exception:
            pass
    return input(f"{label}: ")

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def next_id(df: pd.DataFrame) -> int:
    return 1 if df.empty else int(df['id'].max()) + 1

def is_admin() -> bool:
    u = SESSION["user"]
    return u is not None and u['role'] == 'admin'

def me() -> dict:
    return SESSION["user"]

def me_name() -> str:
    return SESSION["user"]['name'] if SESSION["user"] else ''


# ══════════════════════════════════════════════════════════════
# KEY & I/O HELPER
# ══════════════════════════════════════════════════════════════

def _get_key(key_path: str) -> bytes:
    if os.path.exists(key_path):
        return load_key(key_path)
    # Pastikan direktori key di OS sudah ada sebelum generate
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    return generate_key(key_path)

def _load_enc(path: str, key_path: str, cols: list) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=cols)
    key = _get_key(key_path)
    df  = decrypt_csv(path, key)
    return df.reindex(columns=cols, fill_value='')

def _save_enc(df: pd.DataFrame, path: str, key_path: str, cols: list):
    os.makedirs(BASE_DIR, exist_ok=True)
    key = _get_key(key_path)
    encrypt_csv(df.reindex(columns=cols), path, key)

# ── Users ──
def load_users() -> pd.DataFrame:
    return _load_enc(USER_PATH, KEY_USERS, COLS_USER)

def save_users(df: pd.DataFrame):
    _save_enc(df, USER_PATH, KEY_USERS, COLS_USER)

# ── Credentials ──
def load_creds() -> pd.DataFrame:
    return _load_enc(CREDS_PATH, KEY_CREDS, COLS_CREDS)

def save_creds(df: pd.DataFrame):
    _save_enc(df, CREDS_PATH, KEY_CREDS, COLS_CREDS)

# ── Tunnels ──
def load_tunnels() -> pd.DataFrame:
    return _load_enc(TUNNELS_PATH, KEY_TUNNS, COLS_TUNNEL)

def save_tunnels(df: pd.DataFrame):
    _save_enc(df, TUNNELS_PATH, KEY_TUNNS, COLS_TUNNEL)

# ── Semua user bisa lihat semua data, filter hanya untuk edit/hapus ──
def visible_creds() -> pd.DataFrame:
    return load_creds()

def visible_tunnels() -> pd.DataFrame:
    return load_tunnels()


# ══════════════════════════════════════════════════════════════
# DISPLAY HELPER
# ══════════════════════════════════════════════════════════════

def _mask_pw(val):
    """Admin lihat plaintext, user biasa selalu disembunyikan."""
    return val if is_admin() else '●' * 8

def show_creds(df: pd.DataFrame):
    """Tampilkan semua credential — password hanya terlihat oleh admin."""
    if df.empty:
        print("  (tidak ada data)\n")
        return
    disp = df.copy()
    disp['password'] = disp['password'].apply(_mask_pw)
    print(tabulate(disp, headers='keys', tablefmt='outline', showindex=False))

def show_tunnels(df: pd.DataFrame):
    """Tampilkan semua tunnel — pass_tunnel hanya terlihat oleh admin."""
    if df.empty:
        print("  (tidak ada data)\n")
        return
    disp = df.copy()
    disp['pass_tunnel'] = disp['pass_tunnel'].apply(_mask_pw)
    print(tabulate(disp, headers='keys', tablefmt='pretty', showindex=False))

def show_users(df: pd.DataFrame):
    disp = df[['id', 'name', 'first_name', 'last_name', 'role', 'active']].copy()
    print(tabulate(disp, headers='keys', tablefmt='rounded_outline', showindex=False))


# ══════════════════════════════════════════════════════════════
# INIT — buat default data jika belum ada
# ══════════════════════════════════════════════════════════════

def init():
    os.makedirs(BASE_DIR, exist_ok=True)

    if not os.path.exists(USER_PATH):
        print("[*] Membuat admin default...")
        df = pd.DataFrame([{
            'id': 1, 'name': 'admin', 'password': hash_pw('Admin123!'),
            'first_name': 'Admin', 'last_name': 'Default',
            'role': 'admin', 'active': 'Y',
        }])
        save_users(df)
        print("[+] Admin default → username: admin | password: Admin123!")
        print("[!] Segera ganti password setelah login pertama.\n")

    if not os.path.exists(CREDS_PATH):
        print("[*] Membuat credentials default...")
        df = pd.DataFrame([{
            'id': 1, 'owner': 'admin', 'name': 'sample_db',
            'host': 'localhost', 'port': '8123',
            'username': 'admin', 'password': 'Admin123!',
            'database': 'default', 'methode': 'clickhouse_driver',
            'driver': 'clickhouse', 'use_tunnel': False, 'name_tunnel': None,
        }])
        save_creds(df)

    if not os.path.exists(TUNNELS_PATH):
        print("[*] Membuat tunnels default...")
        df = pd.DataFrame([{
            'id': 1, 'owner': 'admin', 'name': 'sample_tunnel',
            'host_tunnel': '127.0.0.1',
            'user_tunnel': 'sample_tunnel',
            'pass_tunnel': 'sampletunnel123',
        }])
        save_tunnels(df)

def clearout():
    import glob

    files_to_delete = glob.glob(os.path.join(BASE_DIR, "*.enc"))
    
    # Hapus file satu per satu
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"Berhasil dihapus: {file_path}")           
        except Exception as e:
            print(f"Gagal menghapus {file_path}: {e}")
    
    # 2. Perbaikan: Hapus file kunci secara mandiri
    keys_to_delete = [KEY_USERS, KEY_CREDS, KEY_TUNNS]
    for key_path in keys_to_delete:
        try:
            os.remove(key_path)
            print(f"Berhasil menghapus kunci: {key_path}")
        except FileNotFoundError:
            print(f"Kunci tidak ditemukan: {key_path}")
        except Exception as e:
            print(f"Gagal menghapus kunci {key_path}: {e}")
    
    exit()
    
# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════

def login():
    divider("LOGIN")
    usnm = input("Username : ").strip()
    pswd = input_pass("Password", hide=True)

    df  = load_users()
    row = df[(df['name'] == usnm) & (df['active'] == 'Y')]

    if row.empty:
        print("[!] Username tidak ditemukan atau akun nonaktif.\n")
        return

    user = row.iloc[0].to_dict()
    if user['password'] != hash_pw(pswd):
        print("[!] Password salah.\n")
        return

    SESSION["user"] = user
    print(f"\n[+] Selamat datang, {user['first_name']} {user['last_name']}! "
          f"[role: {user['role']}]\n")

def logout():
    SESSION["user"] = None
    print("[+] Logout berhasil.\n")


# ══════════════════════════════════════════════════════════════
# USER MANAGEMENT  (admin only, kecuali update profil sendiri)
# ══════════════════════════════════════════════════════════════

def user_add():
    if not is_admin():
        print("[!] Hanya admin yang bisa menambah user.\n")
        return
    divider("TAMBAH USER")
    df   = load_users()
    name = input("Username baru  : ").strip()
    if not name:
        print("[!] Username tidak boleh kosong.\n"); return
    if not df[df['name'] == name].empty:
        print("[!] Username sudah dipakai.\n"); return

    pswd  = input_pass("Password")
    pswd2 = input_pass("Ulangi password")
    if pswd != pswd2:
        print("[!] Password tidak cocok.\n"); return
    if len(pswd) < 6:
        print("[!] Minimal 6 karakter.\n"); return

    first = input("Nama depan    : ").strip()
    last  = input("Nama belakang : ").strip()
    role  = input("Role (admin/user) [default: user]: ").strip().lower()
    if role not in ('admin', 'user'):
        role = 'user'

    df = pd.concat([df, pd.DataFrame([{
        'id': next_id(df), 'name': name, 'password': hash_pw(pswd),
        'first_name': first, 'last_name': last, 'role': role, 'active': 'Y',
    }])], ignore_index=True)
    save_users(df)
    print(f"[+] User '{name}' ditambahkan sebagai '{role}'.\n")


def user_list():
    if not is_admin():
        print("[!] Akses ditolak.\n"); return
    divider("DAFTAR USER")
    df = load_users()
    if df.empty:
        print("  (belum ada user)\n"); return
    show_users(df)
    print()


def user_update():
    divider("UPDATE USER")
    df = load_users()
    u  = me()

    if is_admin():
        target = input("Username yang diupdate (kosong = diri sendiri): ").strip() or u['name']
    else:
        target = u['name']

    idx_list = df[df['name'] == target].index
    if idx_list.empty:
        print(f"[!] User '{target}' tidak ditemukan.\n"); return
    idx = idx_list[0]

    print(f"\nEdit: {target}  (kosongkan untuk tidak mengubah)\n")
    first = input(f"Nama depan    [{df.at[idx,'first_name']}]: ").strip()
    last  = input(f"Nama belakang [{df.at[idx,'last_name']}]: ").strip()
    pswd  = input_pass("Password baru (kosong = tidak diganti)")

    if first: df.at[idx, 'first_name'] = first
    if last:  df.at[idx, 'last_name']  = last
    if pswd:
        if len(pswd) < 6:
            print("[!] Minimal 6 karakter.\n"); return
        pswd2 = input_pass("Ulangi password baru")
        if pswd != pswd2:
            print("[!] Password tidak cocok.\n"); return
        df.at[idx, 'password'] = hash_pw(pswd)

    # Hanya admin yang bisa ubah role & status user lain
    if is_admin() and target != u['name']:
        r = input(f"Role (admin/user) [{df.at[idx,'role']}]: ").strip().lower()
        if r in ('admin', 'user'):
            df.at[idx, 'role'] = r
        a = input(f"Aktif? (Y/N)      [{df.at[idx,'active']}]: ").strip().upper()
        if a in ('Y', 'N'):
            df.at[idx, 'active'] = a

    save_users(df)
    print(f"[+] User '{target}' berhasil diupdate.\n")
    if target == u['name']:
        SESSION["user"] = df[df['name'] == target].iloc[0].to_dict()


def user_delete():
    if not is_admin():
        print("[!] Akses ditolak.\n"); return
    divider("HAPUS USER")
    df     = load_users()
    show_users(df)
    target = input("\nUsername yang dihapus: ").strip()
    if target == me_name():
        print("[!] Tidak bisa hapus diri sendiri.\n"); return
    idx = df[df['name'] == target].index
    if idx.empty:
        print(f"[!] User '{target}' tidak ditemukan.\n"); return
    if not confirm(f"Yakin hapus user '{target}'?"):
        print("[!] Dibatalkan.\n"); return
    df = df.drop(index=idx).reset_index(drop=True)
    save_users(df)
    print(f"[+] User '{target}' dihapus.\n")


# ══════════════════════════════════════════════════════════════
# TUNNEL CRUD
# ══════════════════════════════════════════════════════════════

def tunnel_add(tunnels: pd.DataFrame, ret=False) -> str:
    """
    Tambah tunnel. Jika ret=True, return nama tunnel (dipanggil dari cred wizard).
    tunnels bisa di-pass langsung (saat dipanggil dari cred) atau None (load sendiri).
    """
    if tunnels is None:
        tunnels = visible_tunnels()
    divider("TAMBAH TUNNEL")
    ids      = next_id(load_tunnels())   # ID global, bukan filtered
    nama     = input("Nama Koneksi  : ").strip()
    host     = input("Host          : ").strip()
    user     = input("Username      : ").strip()
    password = input_pass("Password", hide=not is_admin())

    all_t = load_tunnels()
    new   = pd.DataFrame([{
        'id': ids, 'owner': me_name(), 'name': nama,
        'host_tunnel': host, 'user_tunnel': user, 'pass_tunnel': password,
    }])
    all_t = pd.concat([all_t, new], ignore_index=True)
    save_tunnels(all_t)
    print(f"[+] Tunnel '{nama}' berhasil ditambahkan.\n")
    if ret:
        return nama


def tunnel_edit():
    divider("EDIT TUNNEL")
    tunnels = visible_tunnels()
    show_tunnels(tunnels)

    try:
        ids = int(input("\nID Tunnel yang diedit: "))
    except ValueError:
        print("[!] ID harus angka.\n"); return

    all_t   = load_tunnels()
    focused = all_t[all_t['id'] == ids]
    if focused.empty:
        print(f"[!] ID {ids} tidak ditemukan.\n"); return
    if not is_admin() and focused.iloc[0]['owner'] != me_name():
        print("[!] Bukan milikmu.\n"); return

    f        = focused.iloc[0]
    old_name = f['name']
    print(tabulate(focused, headers='keys', tablefmt='rounded_grid', showindex=False))
    print("Kosongkan untuk tidak mengubah.\n")

    nama = input(f"Nama     [{old_name}]        : ").strip() or old_name
    host = input(f"Host     [{f['host_tunnel']}]: ").strip() or f['host_tunnel']
    user = input(f"Username [{f['user_tunnel']}]: ").strip() or f['user_tunnel']
    pw   = input_pass("Password (kosong=skip)", hide=not is_admin()) or f['pass_tunnel']

    all_t = all_t[all_t['id'] != ids].copy()
    all_t = pd.concat([all_t, pd.DataFrame([{
        'id': ids, 'owner': f['owner'], 'name': nama,
        'host_tunnel': host, 'user_tunnel': user, 'pass_tunnel': pw,
    }])], ignore_index=True)
    all_t = all_t.sort_values('id').reset_index(drop=True)
    save_tunnels(all_t)

    # Update referensi nama di credentials
    if old_name != nama:
        all_c = load_creds()
        all_c['name_tunnel'] = all_c['name_tunnel'].replace(old_name, nama)
        save_creds(all_c)
        print(f"[*] Referensi tunnel '{old_name}' → '{nama}' diperbarui di credentials.")
    print(f"[+] Tunnel '{nama}' berhasil diupdate.\n")


def tunnel_delete():
    divider("HAPUS TUNNEL")
    tunnels = visible_tunnels()
    show_tunnels(tunnels)

    try:
        ids = int(input("\nID Tunnel yang dihapus: "))
    except ValueError:
        print("[!] ID harus angka.\n"); return

    all_t   = load_tunnels()
    focused = all_t[all_t['id'] == ids]
    if focused.empty:
        print(f"[!] ID {ids} tidak ditemukan.\n"); return
    if not is_admin() and focused.iloc[0]['owner'] != me_name():
        print("[!] Bukan milikmu.\n"); return

    tun_nm = focused.iloc[0]['name']
    if not confirm(f"Yakin hapus tunnel '{tun_nm}'?"):
        print("[!] Dibatalkan.\n"); return

    all_t = all_t[all_t['id'] != ids].reset_index(drop=True)
    save_tunnels(all_t)

    # Putuskan referensi di credentials
    all_c = load_creds()
    mask  = all_c['name_tunnel'] == tun_nm
    if mask.any():
        all_c.loc[mask, 'use_tunnel']  = False
        all_c.loc[mask, 'name_tunnel'] = None
        save_creds(all_c)
        print(f"[*] {mask.sum()} credential dilepas dari tunnel ini.")
    print(f"[+] Tunnel '{tun_nm}' dihapus.\n")


# ══════════════════════════════════════════════════════════════
# CREDENTIAL CRUD
# ══════════════════════════════════════════════════════════════

def _pick_driver(default_mtd='', default_drv=''):
    print("Methode:")
    for k, v in MAP_DRIVER.items():
        print(f"  {k}. {v[0]}")
    inp = input("Pilih (kosong = tidak ubah): ").strip()
    return MAP_DRIVER.get(inp, [default_mtd, default_drv])


def _pick_tunnel(key_tunl_unused=None):
    """Interaktif pilih / tambah tunnel milik user ini."""
    tunnels = visible_tunnels()
    if tunnels.empty:
        print("  (belum ada tunnel)")
    else:
        show_tunnels(tunnels)
    inp = input("ID Tunnel (0 = tambah baru, kosong = tidak pakai tunnel): ").strip()
    if inp == '0':
        nama = tunnel_add(tunnels=tunnels, ret=True)
        return True, nama
    elif inp == '':
        return False, None
    else:
        try:
            # Cek dari ALL tunnels agar admin bisa pilih tunnel siapapun
            all_t = load_tunnels() if is_admin() else tunnels
            row   = all_t[all_t['id'] == int(inp)]
            if row.empty:
                print("[!] ID tidak ditemukan, tunnel tidak dipakai.")
                return False, None
            return True, row['name'].values[0]
        except ValueError:
            print("[!] Input tidak valid.")
            return False, None


def cred_add():
    divider("TAMBAH CREDENTIAL")
    all_c  = load_creds()
    ids    = next_id(all_c)
    nama   = input("Nama Koneksi  : ").strip()
    host   = input("Host          : ").strip()
    port   = input("Port          : ").strip()
    user   = input("Username      : ").strip()
    pw     = input_pass("Password", hide=not is_admin())
    db     = input("Database      : ").strip()
    mtd, drv = _pick_driver()

    use_tun, nm_tun = False, None
    if input("Pakai Tunnel? (Y/N): ").strip().upper() == 'Y':
        use_tun, nm_tun = _pick_tunnel()

    new = pd.DataFrame([{
        'id': ids, 'owner': me_name(), 'name': nama,
        'host': host, 'port': port, 'username': user, 'password': pw,
        'database': db, 'methode': mtd, 'driver': drv,
        'use_tunnel': use_tun, 'name_tunnel': nm_tun,
    }])
    all_c = pd.concat([all_c, new], ignore_index=True)
    save_creds(all_c)
    print(f"[+] Credential '{nama}' berhasil ditambahkan.\n")


def cred_edit():
    divider("EDIT CREDENTIAL")
    creds = visible_creds()
    show_creds(creds)

    try:
        ids = int(input("\nID Credential yang diedit: "))
    except ValueError:
        print("[!] ID harus angka.\n"); return

    all_c   = load_creds()
    focused = all_c[all_c['id'] == ids]
    if focused.empty:
        print(f"[!] ID {ids} tidak ditemukan.\n"); return
    if not is_admin() and focused.iloc[0]['owner'] != me_name():
        print("[!] Bukan milikmu.\n"); return

    f = focused.iloc[0]
    print(tabulate(focused, headers='keys', tablefmt='rounded_grid', showindex=False))
    print("Kosongkan untuk tidak mengubah.\n")

    nama = input(f"Nama     [{f['name']}]    : ").strip() or f['name']
    host = input(f"Host     [{f['host']}]    : ").strip() or f['host']
    port = input(f"Port     [{f['port']}]    : ").strip() or f['port']
    user = input(f"Username [{f['username']}]: ").strip() or f['username']
    pw   = input_pass("Password (kosong=skip)", hide=not is_admin()) or f['password']
    db   = input(f"Database [{f['database']}]: ").strip() or f['database']
    mtd, drv = _pick_driver(f['methode'], f['driver'])

    use_tun, nm_tun = f['use_tunnel'], f['name_tunnel']
    if input("Ubah pengaturan tunnel? (Y/N): ").strip().upper() == 'Y':
        use_tun, nm_tun = _pick_tunnel()

    all_c = all_c[all_c['id'] != ids].copy()
    all_c = pd.concat([all_c, pd.DataFrame([{
        'id': ids, 'owner': f['owner'], 'name': nama,
        'host': host, 'port': port, 'username': user, 'password': pw,
        'database': db, 'methode': mtd, 'driver': drv,
        'use_tunnel': use_tun, 'name_tunnel': nm_tun,
    }])], ignore_index=True)
    all_c = all_c.sort_values('id').reset_index(drop=True)
    save_creds(all_c)
    print(f"[+] Credential '{nama}' berhasil diupdate.\n")


def cred_delete():
    divider("HAPUS CREDENTIAL")
    creds = visible_creds()
    show_creds(creds)

    try:
        ids = int(input("\nID Credential yang dihapus: "))
    except ValueError:
        print("[!] ID harus angka.\n"); return

    all_c   = load_creds()
    focused = all_c[all_c['id'] == ids]
    if focused.empty:
        print(f"[!] ID {ids} tidak ditemukan.\n"); return
    if not is_admin() and focused.iloc[0]['owner'] != me_name():
        print("[!] Bukan milikmu.\n"); return

    nama = focused.iloc[0]['name']
    if not confirm(f"Yakin hapus credential '{nama}'?"):
        print("[!] Dibatalkan.\n"); return

    all_c = all_c[all_c['id'] != ids].reset_index(drop=True)
    save_creds(all_c)
    print(f"[+] Credential '{nama}' dihapus.\n")


# ══════════════════════════════════════════════════════════════
# MENU
# ══════════════════════════════════════════════════════════════

HEADER = """
╔══════════════════════════════════════════════════════╗
║        Muara Data — Credential Manager CLI           ║
╚══════════════════════════════════════════════════════╝"""

def print_header():
    print(HEADER)
    u = me()
    if u:
        tag = f"  ● Login sebagai : {u['first_name']} {u['last_name']}  [{u['role'].upper()}]"
        print(tag)
    divider()

def menu_guest():
    print("  [1] Login")
    print("  [0] Keluar")

def menu_main():
    u = me()
    admin = u['role'] == 'admin'
    print("  ── Profil ─────────────────────────")
    print("  [1] Update profil saya")
    print("  [2] Logout")
    if admin:
        print("\n  ── User Management (admin) ─────────")
        print("  [3] Tambah user")
        print("  [4] Lihat semua user")
        print("  [5] Edit user")
        print("  [6] Hapus user")
    print("\n  ── Credentials ─────────────────────")
    print("  [7] Lihat credentials")
    print("  [8] Tambah credential")
    print("  [9] Edit credential")
    print("  [10] Hapus credential")
    print("\n  ── Tunnels ─────────────────────────")
    print("  [11] Lihat tunnels")
    print("  [12] Tambah tunnel")
    print("  [13] Edit tunnel")
    print("  [14] Hapus tunnel")
    print("\n  ── Reset ─────────────────────────")
    print("  [15] Clear-out Credentials")
    print("\n  [0] Keluar")


# ══════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════

def main():
    init()
    clear()

    while True:
        args = sys.argv[1:]
        
        if args:
            command = args[0].lower()
            if command == "peek":
                divider("CREDENTIALS"); show_creds(visible_creds()); print(); sys.exit(0)
            
            elif command == "tunnel":
                divider("TUNNELS"); show_tunnels(visible_tunnels()); print(); sys.exit(0)
            
            elif command == "test":
                import subprocess
                
                target_file = os.path.join(BASE_DIR, "..", "..", "tests", "unit_test.py")
                target_file = os.path.normpath(target_file)
                subprocess.run(["python", target_file])
                exit()
            
            elif command == "reset":
                clearout()
            
            elif command == "help":
                import textwrap 
                
                pesan_help = """
                    DAFTAR PERINTAH MUARADB:
                    ---------------------------------------------
                    peek   : Mengintip isi credential tabel
                    tunnel : Mengintip isi konfigurasi ssh tunnel
                    test   : Menguji koneksi database
                    reset  : Menghapus total configurasi credentials
                    ---------------------------------------------
                """
                print(textwrap.dedent(pesan_help))
                sys.exit(0)
            
            else:
                print(f"Perintah '{command}' tidak dikenal.")
                sys.exit(0)
        
        print_header()
        
        if not me():
            menu_guest()
            divider()
            p = input("Pilih: ").strip()
            if   p == '1': login()
            elif p == '0': print("Sampai jumpa!\n"); sys.exit(0)
            else:          print("[!] Pilihan tidak valid.\n")
            continue

        # ── Sudah login ──
        menu_main()
        divider()
        p = input("Pilih: ").strip()

        # Profil
        if   p == '1': user_update()
        elif p == '2': logout()

        # User management (admin only)
        elif p == '3': user_add()
        elif p == '4': user_list()
        elif p == '5': user_update()         # admin bisa pilih target
        elif p == '6': user_delete()

        # Credentials
        elif p == '7':
            divider("CREDENTIALS"); show_creds(visible_creds()); print()
        elif p == '8':  cred_add()
        elif p == '9':  cred_edit()
        elif p == '10': cred_delete()

        # Tunnels
        elif p == '11':
            divider("TUNNELS"); show_tunnels(visible_tunnels()); print()
        elif p == '12': tunnel_add(tunnels=None)
        elif p == '13': tunnel_edit()
        elif p == '14': tunnel_delete()
        
        elif p == '15': clearout()

        elif p == '0':
            print("Sampai jumpa!\n"); sys.exit(0)
        else:
            print("[!] Pilihan tidak valid.\n")


if __name__ == '__main__':
    main()