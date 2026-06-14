import numpy as np
import pandas as pd
from iriis_connection_library.core.insert_base import BaseInserter
from time import sleep

class ClickHouseInserter(BaseInserter):
    
    def __init__(self, driver):
        self.driver = driver


    def insert(self, df, table, columns, truncate=False):
        IGNORE = {"", np.nan, None, np.inf, -np.inf, 'nan', 'NaN', 'no_need', 'No Need', 'None'}
    
        def isna_safe_scalar(x):
            # pd.isna untuk scalar saja; jika x koleksi, kembalikan False.
            if isinstance(x, (list, tuple, np.ndarray, set, dict)):
                return False
            try:
                return bool(pd.isna(x))
            except Exception:
                return False

        def should_null(x):
            # Jika koleksi (list/tuple/ndarray), jangan dinilai sebagai NA di sini.
            # Elemen koleksi biasanya ditujukan ke kolom Array(String).
            if isinstance(x, (list, tuple, np.ndarray)):
                return False
            if x is None:
                return True 
            if isna_safe_scalar(x):
                return True
            
            return x in IGNORE # Membership: gunakan set agar aman untuk semua scalar hashable
        
        def normalize_value(x):
            if should_null(x):
                return None
            if isinstance(x, np.ndarray):
                return x.tolist()          # np.ndarray → Python list
            if isinstance(x, tuple):
                return list(x)             # tuple → Python list
            if isinstance(x, (np.integer,)):
                return int(x)              # np scalar → Python int
            if isinstance(x, (np.floating,)):
                return float(x)            # np scalar → Python float
            return x
        
        col_list = ", ".join(columns)
        
        # data = [np.array([None if should_null(x) else x for x in df[col]], dtype=object) for col in columns]
        # data = [build_column(col) for col in columns]
        # data = [[normalize_value(x) for x in df[col]] for col in columns]
        data = [np.array([normalize_value(x) for x in df[col]], dtype=object) for col in columns]
        
        if truncate:
            print(f"Clear Out {table}")
            self.driver.execute(f"TRUNCATE TABLE {table}")
            sleep(10)
        
        self.driver.insert_dataframe(data, table, col_list)        
        return True