import os
import pandas as pd
import io
from cryptography.fernet import Fernet
from pathlib import Path

# ──────────────────────────────────────────────
# KEY MANAGEMENT
# ──────────────────────────────────────────────

def generate_key(key_path: str = None) -> bytes:
    """Generate master key dan simpan ke file (jalankan sekali saja)."""
    key = Fernet.generate_key()
    if key_path:
        Path(key_path).write_bytes(key)
        print(f"Key disimpan ke: {key_path}")
    return key

def load_key(key_path: str = None) -> bytes:
    """
    Load key dari env var atau file.
    Priority: ENV VAR > key file
    """
    # 1. Coba dari environment variable (paling aman untuk production)
    env_key = os.environ.get("CREDS_MASTER_KEY")
    if env_key:
        return env_key.encode()
    
    # 2. Fallback ke key file
    if key_path and os.path.exists(key_path):
        return Path(key_path).read_bytes()
    
    raise RuntimeError(
        "Master key tidak ditemukan. "
        "Set env var CREDS_MASTER_KEY atau sediakan key file."
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
