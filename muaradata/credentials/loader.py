import os
import hashlib
import pandas as pd
from pathlib import Path
import getpass

from .cripter import _key_path, load_key, decrypt_csv

# ── Path .enc (tetap di folder project) ──
_USER_ENGINE = getpass.getuser()

BASE_DIR     = os.path.dirname(os.path.dirname(__file__))

CREDS_PATH   = os.path.join(BASE_DIR, "credentials", "credentials.enc")
TUNNELS_PATH = os.path.join(BASE_DIR, "credentials", "tunnels.enc")

KEY_CREDS    = _key_path(f"{_USER_ENGINE}_muaradata_creds_store")
KEY_TUNNS    = _key_path(f"{_USER_ENGINE}_muaradata_tunns_store")

# ══════════════════════════════════════════════
# LOADER FUNCTIONS
# ══════════════════════════════════════════════

def load_credentials(name: str) -> dict:
    key = load_key(KEY_CREDS)
    df  = decrypt_csv(CREDS_PATH, key)

    row = df[df["name"] == name]
    if row.empty:
        raise ValueError(f"Credential '{name}' not found")

    row = row.copy()
    row["use_tunnel"] = row["use_tunnel"].fillna("False")
    row["use_tunnel"] = row["use_tunnel"].replace({"True": True, "False": False})

    return row.iloc[0].to_dict()


def load_tunnels(name: str) -> dict:
    key = load_key(KEY_TUNNS)
    df  = decrypt_csv(TUNNELS_PATH, key)

    row = df[df["name"] == name]
    return {} if row.empty else row.iloc[0].to_dict()

