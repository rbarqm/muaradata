import pandas as pd

def pandas_dtypes(df):
    df = df.copy()
    df.columns = df.columns.str.lower()
    
    dtypes = {}
    for col, dtype in df.dtypes.items():
        dtypes[col] = str(dtype).upper()
    return dtypes, df
