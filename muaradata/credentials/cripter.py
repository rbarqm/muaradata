import os
import hashlib
import pandas as pd
import io
from cryptography.fernet import Fernet
from pathlib import Path
from platformdirs import user_config_dir

# ──────────────────────────────────────────────
# KEY MANAGEMENT
# ──────────────────────────────────────────────
#
#  Penamaan env var untuk production:
#  Tiap key file punya env var sendiri, namanya di-derive dari
#  nama file (tanpa ekstensi) agar tidak perlu hardcode.
#
#  Contoh: file key  = 0e8ebdd27d82.dat
#          env var   = IRIIS_0E8EBDD27D82
#
#  Cara set (Linux/macOS):
#    export IRIIS_0E8EBDD27D82="<base64-fernet-key>"
#
#  Cara set (Windows):
#    $Env:IRIIS_0E8EBDD27D82="<base64-fernet-key>"
#
# ──────────────────────────────────────────────

_KEY_DIR   = user_config_dir(appname="muaradata", appauthor=False)

def _key_path(seed: str) -> str:
    filename = hashlib.sha1(seed.encode()).hexdigest()[:12] + ".dat"
    return os.path.join(_KEY_DIR, filename)


def _env_var_name(key_path: str) -> str:
    stem = Path(key_path).stem.upper()
    return f"MuaraData_{stem}"


def generate_key(key_path: str = None) -> bytes:
    key = Fernet.generate_key()
    if key_path:
        p = Path(key_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(key)
        # Proteksi permission: hanya owner yang bisa baca (Unix)
        try:
            p.chmod(0o600)
        except Exception:
            pass  # Windows tidak support chmod, skip
    return key


def load_key(key_path: str = None) -> bytes:
    # 1. Env var spesifik (derived dari nama file key)
    if key_path:
        env_name = _env_var_name(key_path)
        val = os.environ.get(env_name)
        if val:
            return val.encode()

    # 2. Env var generik sebagai fallback
    val = os.environ.get("MUARADATA_MASTER")
    if val:
        return val.encode()

    # 3. Baca dari file
    if key_path and os.path.exists(key_path):
        return Path(key_path).read_bytes()

    raise RuntimeError(
        f"Key tidak ditemukan.\n"
        f"  File  : {key_path}\n"
        f"  Env   : {_env_var_name(key_path) if key_path else 'MUARADATA_MASTER'}\n"
        f"Jalankan ulang agar key di-generate otomatis, "
        f"atau set env var di atas."
    )


# ──────────────────────────────────────────────
# ENCRYPT / DECRYPT CSV
# ──────────────────────────────────────────────

def encrypt_csv(df: pd.DataFrame, output_path: str, key: bytes) -> None:
    """Enkripsi DataFrame sebagai CSV terenkripsi."""
    fernet = Fernet(key)
    
    # Serialize df → bytes (tanpa menyentuh disk)
    csv_bytes = df.to_csv(sep=';', index=False).encode('utf-8')
    
    # Enkripsi
    encrypted = fernet.encrypt(csv_bytes)
    
    Path(output_path).write_bytes(encrypted)
    # print(f"Tersimpan terenkripsi: {output_path}")


def decrypt_csv(encrypted_path: str, key: bytes) -> pd.DataFrame:
    """Baca file terenkripsi → DataFrame."""
    fernet = Fernet(key)
    
    encrypted = Path(encrypted_path).read_bytes()
    csv_bytes = fernet.decrypt(encrypted)  # Akan raise exception jika key salah
    
    return pd.read_csv(io.BytesIO(csv_bytes), sep=';')
