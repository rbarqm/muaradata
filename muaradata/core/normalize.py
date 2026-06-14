import pandas as pd
import numpy as np

IGNORE = {"", np.nan, None, np.inf, -np.inf, 'nan', 'NaN', 'no_need', 'No Need', 'None'}

def normalize_df(out, columns):
    
    def to_string_list(x):
        # Normalisasi ke list[str]
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return np.array([], dtype=str)
        
        if isinstance(x, (list, tuple, np.ndarray)):
            return np.array(["" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v) for v in x], dtype=str)
        else:
            s = str(x).strip()
            items = [t.strip() for t in s.split(",") if t.strip()] if s else []
            return np.array(items, dtype=str)
    
    def _flatten_cols(cols):
        out_list = []
        for c in cols:
            if isinstance(c, (list, tuple)):
                out_list.extend(c)
            else:
                out_list.append(c)
        return out_list
    
    
    kol_all = columns.get('all', [])
    kol_flt = columns.get('float', [])
    kol_int = columns.get('integer', [])
    kol_arr = columns.get('array', [])
    kol_dtt = columns.get('datetime', [])
    kol_str = columns.get('string', [])
    
    kol_tbl = set(_flatten_cols(kol_all))
    
    if not kol_str:
        kol_str = [col for col in kol_tbl if col not in kol_flt and col not in kol_int and col not in kol_arr and col not in kol_dtt]
    
    # Apply conversions
    for col in kol_flt:
        if col not in kol_tbl:
            continue
        out[col] = pd.to_numeric(out[col], errors='coerce').fillna(0).astype('Float64')
        out[col] = out[col].apply(lambda x: float(x) if np.isfinite(x) else x)

    for col in kol_int:
        if col not in kol_tbl:
            continue
        out[col] = pd.to_numeric(out[col], errors='coerce') # Konversi ke numeric, ubah error jadi NaN
        out[col] = out[col].apply(lambda x: int(x) if pd.notna(x) else pd.NA) # Gunakan apply untuk ubah ke int jika bukan NaN
        out[col] = out[col].astype('Int64') # Set tipe data ke Int64 (nullable integer)
    
    for col in kol_arr:
        if col not in kol_tbl:
            continue
        out[col] = out[col].apply(to_string_list)

    for col in kol_dtt:
        if col not in kol_tbl:
            continue
        out[col] = pd.to_datetime(out[col], errors='coerce')
    
    for col in kol_str:
        if col not in kol_tbl:
            continue
        out[col] = out[col].astype(str)
        out[col] = out[col].replace(IGNORE, np.nan)
    
    data = out[kol_all].copy()
    
    # Final safeguard for array columns to ensure they are numpy arrays of strings
    for col in kol_arr:
        if col in data.columns:
            data[col] = data[col].apply(lambda x: np.array(x, dtype=str) if isinstance(x, (list, np.ndarray)) else np.array([], dtype=str))

    return data
