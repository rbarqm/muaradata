import os
import pandas as pd

from .cripter import load_key, decrypt_csv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def load_credentials(name: str) -> dict:
    key_path = os.path.join(BASE_DIR, "credentials", "kunci_creds.key")
    key = load_key(key_path)
    
    path = os.path.join(BASE_DIR, "credentials", "credentials.enc")
    df = decrypt_csv(path, key)
    row = df[df["name"] == name]
    
    if row.empty:
        raise ValueError(f"Credential '{name}' not found")
    
    row["use_tunnel"] = row["use_tunnel"].fillna("False")
    row["use_tunnel"] = row["use_tunnel"].replace({"True": True, "False": False})
    
    return row.iloc[0].to_dict()

def load_tunnels(name: str) -> dict:
    key_path = os.path.join(BASE_DIR, "credentials", "kunci_tunnel.key")
    key = load_key(key_path)
    
    path = os.path.join(BASE_DIR, "credentials", "tunnels.enc")
    df = decrypt_csv(path, key)    
    row = df[df["name"] == name]
    
    return {} if row.empty else row.iloc[0].to_dict()
