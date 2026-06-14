import warnings
warnings.filterwarnings("ignore")

import os
import sys
import hashlib
import socket
import pandas as pd
from tabulate import tabulate
from time import sleep
from platformdirs import user_config_dir


BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CRED_DIR  = os.path.abspath(os.path.join(BASE_DIR, '..', 'muaradata', 'credentials'))

# ── Path .dat (di system config dir OS, sama persis dengan app.py) ──
_KEY_DIR = user_config_dir(appname="muaradata", appauthor=False)

def _key_path(seed: str) -> str:
    filename = hashlib.sha1(seed.encode()).hexdigest()[:12] + ".dat"
    return os.path.join(_KEY_DIR, filename)

CREDS_PATH   = os.path.join(CRED_DIR, 'credentials.enc')
TUNNELS_PATH = os.path.join(CRED_DIR, 'tunnels.enc')

KEY_CREDS = _key_path("muaradata_creds_store")
KEY_TUNNS = _key_path("muaradata_tunns_store")


# Tambahkan cred_dir ke path agar cripter bisa di-import
if CRED_DIR not in sys.path:
    sys.path.insert(0, CRED_DIR)

try:
    from cripter import load_key, decrypt_csv
except ImportError as e:
    print(f"[ERROR] Gagal import cripter dari '{CRED_DIR}': {e}")
    sys.exit(1)

try:
    from iriis_connection_library import fetch_data, fetch_data, insert_data
except ImportError as e:
    print(f"[ERROR] Gagal import iriis_connection_library: {e}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════
# HELPER UI
# ══════════════════════════════════════════════════════════════

STATUS_OK   = "[  OK  ]"
STATUS_FAIL = "[ FAIL ]"
STATUS_ERR  = "[ ERR  ]"

def divider(title="", width=58):
    if title:
        pad = width - len(title) - 4
        print(f"\n─── {title} {'─' * max(pad, 2)}")
    else:
        print("─" * width)

def ask_id(prompt="Conn ID: ") -> int:
    """Input ID dengan validasi. Return None kalau user cancel/invalid."""
    for attempt in range(3):
        raw = input(prompt).strip()
        if not raw:
            print("[!] ID tidak boleh kosong.")
            continue
        try:
            return int(raw)
        except ValueError:
            print(f"[!] '{raw}' bukan angka yang valid.")
    print("[!] Terlalu banyak input tidak valid. Kembali ke menu.")
    return None


# ══════════════════════════════════════════════════════════════
# LOADER — decrypt & validasi file
# ══════════════════════════════════════════════════════════════

def load_creds_data() -> pd.DataFrame:
    """Load credentials.enc → DataFrame. Return None jika gagal."""
    for path in [CREDS_PATH, KEY_CREDS]:
        if not os.path.exists(path):
            print(f"{STATUS_ERR} File tidak ditemukan: {path}")
            return None
    try:
        key  = load_key(KEY_CREDS)
        data = decrypt_csv(CREDS_PATH, key)
        return data.sort_values(by=['id']).reset_index(drop=True)
    except Exception as e:
        print(f"{STATUS_ERR} Gagal membaca credentials: {e}")
        return None

def load_tunnels_data() -> pd.DataFrame:
    """Load tunnels.enc → DataFrame. Return None jika gagal."""
    for path in [TUNNELS_PATH, KEY_TUNNS]:
        if not os.path.exists(path):
            print(f"{STATUS_ERR} File tidak ditemukan: {path}")
            return None
    try:
        key  = load_key(KEY_TUNNS)
        data = decrypt_csv(TUNNELS_PATH, key)
        return data.sort_values(by=['id']).reset_index(drop=True)
    except Exception as e:
        print(f"{STATUS_ERR} Gagal membaca tunnels: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# TEST FUNCTIONS
# ══════════════════════════════════════════════════════════════

def test_db():
    """Test koneksi ke database credential yang dipilih."""
    divider("TEST DB CONNECTION")

    data = load_creds_data()
    if data is None:
        return

    # Tampilkan kolom yang relevan saja, sembunyikan password
    display_cols = [c for c in ['id', 'owner', 'name', 'host', 'port',
                                'methode', 'use_tunnel', 'name_tunnel']
                    if c in data.columns]
    print(tabulate(data[display_cols], headers='keys',
                   tablefmt='pretty', showindex=False))

    # Validasi input ID
    conn_id = ask_id("Pilih Conn ID: ")
    if conn_id is None:
        return

    row = data[data['id'] == conn_id]
    if row.empty:
        print(f"{STATUS_FAIL} ID {conn_id} tidak ditemukan.\n")
        return

    nama_kon = row.iloc[0]['name']
    print(f"\n[*] Menguji koneksi ke: {nama_kon} ...")

    try:
        sql    = f"SELECT 'Connected to {nama_kon}' AS response"
        result = fetch_data(query=sql, aim=nama_kon)
        print(f"{STATUS_OK} Koneksi berhasil!")
        print(tabulate(result, headers='keys', tablefmt='rounded_outline',
                       showindex=False))
    except Exception as e:
        print(f"{STATUS_FAIL} Koneksi gagal: {e}\n")


def _check_port(host: str, port: int = 22, timeout: int = 3) -> bool:
    """Cek apakah host:port bisa dijangkau via TCP."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def test_tunnel():
    """Test konektivitas TCP ke host tunnel yang dipilih."""
    divider("TEST TUNNEL CONNECTION")

    data = load_tunnels_data()
    if data is None:
        return

    display_cols = [c for c in ['id', 'owner', 'name', 'host_tunnel', 'user_tunnel']
                    if c in data.columns]
    print(tabulate(data[display_cols], headers='keys',
                   tablefmt='pretty', showindex=False))

    conn_id = ask_id("Pilih Conn ID: ")
    if conn_id is None:
        return

    row = data[data['id'] == conn_id]
    if row.empty:
        print(f"{STATUS_FAIL} ID {conn_id} tidak ditemukan.\n")
        return

    tunnel  = row.iloc[0]
    nama    = tunnel['name']
    host    = tunnel['host_tunnel']

    # Port bisa dikustomisasi
    raw_port = input("Port [default: 22]: ").strip()
    try:
        port = int(raw_port) if raw_port else 22
    except ValueError:
        print("[!] Port tidak valid, menggunakan 22.")
        port = 22

    print(f"\n[*] Menguji tunnel '{nama}' → {host}:{port} ...")
    ok = _check_port(host, port)

    if ok:
        print(f"{STATUS_OK} Tunnel aktif dan bisa dijangkau: {host}:{port}\n")
    else:
        print(f"{STATUS_FAIL} Tunnel tidak merespons di {host}:{port}\n")


def test_all():
    """Jalankan test semua credential dan tunnel sekaligus."""
    divider("TEST ALL — CREDENTIALS")
    creds = load_creds_data()
    if creds is not None and not creds.empty:
        results = []
        for _, row in creds.iterrows():
            nama = row['name']
            print(f"[*] Testing DB: {nama} ...", end=' ', flush=True)
            try:
                fetch_data(f"SELECT 1", aim=nama)
                print(STATUS_OK)
                results.append({'name': nama, 'type': 'db', 'status': 'OK'})
            except Exception as e:
                print(f"{STATUS_FAIL} ({e})")
                results.append({'name': nama, 'type': 'db', 'status': f'FAIL: {e}'})
    else:
        print("  (tidak ada credential)")
        results = []

    divider("TEST ALL — TUNNELS")
    tunnels = load_tunnels_data()
    if tunnels is not None and not tunnels.empty:
        for _, row in tunnels.iterrows():
            nama = row['name']
            host = row['host_tunnel']
            print(f"[*] Testing Tunnel: {nama} ({host}:22) ...", end=' ', flush=True)
            ok = _check_port(host, 22)
            status = STATUS_OK if ok else STATUS_FAIL
            print(status)
            results.append({'name': nama, 'type': 'tunnel', 'status': 'OK' if ok else 'FAIL'})
    else:
        print("  (tidak ada tunnel)")

    divider("SUMMARY")
    if results:
        print(tabulate(results, headers='keys', tablefmt='rounded_outline', showindex=False))
    print()


# ══════════════════════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════════════════════

MENU = """
╔══════════════════════════════════════════════════════╗
║              IRIIS — Connection Tester               ║
╠══════════════════════════════════════════════════════╣
║  [1]  Test Tunnel                                    ║
║  [2]  Test DB Connection                             ║
║  [0]  Exit                                           ║
╚══════════════════════════════════════════════════════╝"""

SWITCHER = {
    '1': test_tunnel,
    '2': test_db,
    # '3': test_all,
}

def main():
    while True:
        print(MENU)
        value = input("Pilih: ").strip()

        if value == '0':
            print("\nBye!\n")
            sys.exit(0)

        func = SWITCHER.get(value)
        if func is None:
            print("[!] Pilihan tidak valid.\n")
            continue

        func()

        input("Tekan Enter untuk kembali ke menu...")


if __name__ == '__main__':
    main()
