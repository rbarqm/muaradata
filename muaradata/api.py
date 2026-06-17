import warnings
warnings.filterwarnings("ignore")

import pandas as pd

from rich.console import Console

from .credentials.loader import load_credentials
from .credentials.loader import load_tunnels
from .core.registry import REGISTRY
from .core.insert_registry import INSERT_REGISTRY
from .core.normalize import normalize_df
from .core.table_registry import TABLE_REGISTRY
from .core.retry import with_retry, RetryConfig

"""
    Author     : Redian Barqy Muhammad <rbm.eki@gmail.com>
    Copyright  : Copyright 2024, MuaraData Project
"""

retry_cfg_run = RetryConfig(retries=5, delay=5, backoff=2)
retry_cfg_exec = RetryConfig(retries=1, delay=2, backoff=2)

console = Console(log_path=False)

def get_client(aim, exec=False):
    creds = load_credentials(aim)
    driver_name = creds["driver"]   # contoh: clickhouse / postgresql
    use_tunnel = creds["use_tunnel"]   # contoh: tunnel_1
    tunnels = 'None'
    if use_tunnel:
        tunnels = load_tunnels(creds["name_tunnel"])
    
    driver_cls = REGISTRY[driver_name]
    client = driver_cls(creds, tunnels) 
    client.connect()
    return client, driver_name


@with_retry(retry_cfg_run)
def fetch_data(query, aim="iriis_ch"):
    client, driver = get_client(aim)
    with console.status("[bold green]Executing Query") as status:
        df = client.query(query)
        
        # console.log("Data berhasil diambil!")
    return df
    
def run_query(query, aim):
    warnings.filterwarnings("default", category=DeprecationWarning)
    warnings.warn(
        "USANG: Fungsi [run_query] akan dihapus secara permanen pada rilis versi masa depan. "
        "Silakan gunakan fungsi [fetch_data] untuk menjaga keberlanjutan kode Anda.",
        category=DeprecationWarning,
        stacklevel=2
    )
    # print("⚠️ DEPRECATED / USANG: Fungsi [run_query] akan dihapus secara permanen pada rilis versi masa depan. Silakan gunakan fungsi [fetch_data] untuk menjaga keberlanjutan kode Anda.")
    return fetch_data(query=query, aim=aim)


@with_retry(retry_cfg_exec)
def exec_query(query, aim="iriis_ch"):
    client, driver = get_client(aim)
    with console.status("Executing Query") as status:
        client.execute(query)        
        console.log("Query successfully executed!")
    return True
    
def run_exec(query, aim):
    warnings.filterwarnings("default", category=DeprecationWarning)
    warnings.warn(
        "USANG: Fungsi [run_exec] akan dihapus secara permanen pada rilis versi masa depan. "
        "Silakan gunakan fungsi [exec_query] untuk menjaga keberlanjutan kode Anda.",
        category=DeprecationWarning,
        stacklevel=2
    )
    # print("⚠️ DEPRECATED / USANG: Fungsi [run_exec] akan dihapus secara permanen pada rilis versi masa depan. Silakan gunakan fungsi [exec_query] untuk menjaga keberlanjutan kode Anda.")
    return exec_query(query, aim)


def insert_data(result, aim="iriis_ch", nama_table=None, nama_table_ch=None, nama_table_pg=None, kolom=None, truncate=False, rename_kolom=None):
    if kolom is None:
        raise ValueError("Missing required parameter: kolom")
    
    if rename_kolom:
        result = result.rename(columns=rename_kolom)
    
    if kolom=='auto':
        string_cols = [col for col in result.select_dtypes(include=['object']).columns if not any(isinstance(val, list) for val in result[col].dropna())]

        array_cols = [col for col in result.select_dtypes(include=['object']).columns if any(isinstance(val, list) for val in result[col].dropna())]
        
        kolom = {
            'all': result.columns.tolist(),
            'float': result.select_dtypes(include=['float64', 'float32']).columns.tolist(),
            'integer': result.select_dtypes(include=['int64', 'int32', 'int16', 'int8']).columns.tolist(),
            'datetime': result.select_dtypes(include=['datetime']).columns.tolist(),
            # 'string': result.select_dtypes(include=['object']).columns.tolist(),
            'string': string_cols,
            'array': array_cols,
        }

    client, driver = get_client(aim=aim)
    inserter_cls = INSERT_REGISTRY[driver]
    inserter = inserter_cls(client)
    df = normalize_df(result, kolom)
    if nama_table is None:
        nama_table = nama_table_ch if driver=='clickhouse' else nama_table_pg
    inserter.insert(df, nama_table, kolom["all"], truncate)
    
    return True


def generate_table(
    df,
    aim="iriis_ch",
    nama_table=None,    
    drop_table=True,
    ingest_data=True,    
    **kwargs,
):  
    arguments = [df, aim, nama_table]
    
    # Cek apakah ada yang bernilai None atau kosong
    if not all(arg is not None for arg in arguments):
        raise ValueError("Semua argumen wajib diisi dan tidak boleh None!")
    
    client, driver = get_client(aim, exec=True)
    generator = TABLE_REGISTRY[driver](client)
    generator.generate(df, nama_table, drop_table=drop_table, **kwargs)
    
    DRIVER_TABLE_ARG = {
        "clickhouse": "nama_table_ch",
        "postgresql": "nama_table_pg",
        "mysql": "nama_table",
    }
    
    table_kwargs = {arg: None for arg in DRIVER_TABLE_ARG.values()}
    table_kwargs[DRIVER_TABLE_ARG[driver]] = nama_table
    
    if ingest_data:
        insert_data(result=df, aim=aim, kolom='auto', **table_kwargs)
    
    return True


def copy_table(
    nama_table_source: str,
    aim_source: str,
    nama_table_destination: str,
    aim_destination: str,
    drop_table: bool = True,
    with_data: bool = False,
    sample_rows: int = 100,
    **kwargs,
):
    """
    Menyalin struktur tabel dari satu server ke server lain, lintas platform
    dan lintas database (PostgreSQL ↔ ClickHouse atau driver apapun yang
    terdaftar di REGISTRY).
 
    Cara kerja:
      1. Ambil sample baris dari tabel source untuk membaca struktur kolom
         dan tipe data (bukan full data, kecuali with_data=True).
      2. Resolve driver destination dari kredensial aim_destination.
      3. Buat tabel di destination via generate_table() dengan kolom yang
         sudah dinormalisasi. Ingest data hanya jika with_data=True.
 
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
 
    Returns:
        True jika proses selesai tanpa error.
 
    Raises:
        ValueError: Jika driver destination tidak dikenali atau tidak didukung.
        Exception:  Meneruskan exception dari fetch_data / generate_table.
 
    Contoh penggunaan:
        # Salin struktur saja, dari PostgreSQL ke ClickHouse
        copy_table("public.tx_ticket", "iriis_pg", "staging_area.tx_ticket", "iriis_ch")
 
        # Salin struktur + data sample, dari ClickHouse ke PostgreSQL
        copy_table(
            "staging_area.tx_ticket", "iriis_ch",
            "public.tx_ticket", "iriis_pg",
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
    """
    
    
    # ---------------------------------------------------------------------------
    # Pemetaan tipe DB → dtype Pandas
    # Dipakai oleh _fetch_typed_sample untuk cast kolom setelah fetch.
    # Tambahkan entri baru di sini jika ada tipe DB yang belum terdaftar.
    # ---------------------------------------------------------------------------
     
    _CH_TO_PANDAS = {
        # Integer
        "int8": "Int8",   "int16": "Int16",  "int32": "Int32",  "int64": "Int64",
        "uint8": "UInt8", "uint16": "UInt16","uint32": "UInt32","uint64": "UInt64",
        # Float
        "float32": "float32", "float64": "float64",
        # String / text
        "string": "object",   "fixedstring": "object",
        # Datetime
        "datetime": "datetime64[ns]",  "datetime64": "datetime64[ns]",
        "date":     "datetime64[ns]",  "date32":     "datetime64[ns]",
        # Boolean
        "bool": "bool",  "uint8": "bool",
    }
    
    _PG_TO_PANDAS = {
        # Integer
        "smallint": "Int16",  "integer": "Int32",   "int": "Int32",
        "bigint":   "Int64",  "smallserial": "Int16","serial": "Int32",
        "bigserial":"Int64",
        # Float / numeric
        "real": "float32",  "double precision": "float64",  "float": "float64",
        "numeric": "float64", "decimal": "float64",
        # String / text
        "character varying": "object", "varchar": "object",
        "character": "object", "char": "object", "text": "object", "name": "object",
        "uuid": "object",
        # Datetime
        "timestamp without time zone": "datetime64[ns]",
        "timestamp with time zone":    "datetime64[ns]",
        "timestamp": "datetime64[ns]",
        "date":      "datetime64[ns]",
        "time":      "object",
        # Boolean
        "boolean": "bool",
        # JSON / array → object
        "json": "object",  "jsonb": "object",  "array": "object",
    }
    
    
    def _parse_ch_type(raw_type: str) -> str:
        """
        Ekstrak tipe dasar dari tipe ClickHouse yang bisa nested.
     
        Contoh:
            "Nullable(Int64)"      → "int64"
            "LowCardinality(String)" → "string"
            "Array(String)"        → "array"
            "Int32"                → "int32"
        """
        t = raw_type.strip()
        # Unwrap Nullable(...) dan LowCardinality(...)
        for wrapper in ("Nullable", "LowCardinality"):
            if t.startswith(wrapper + "(") and t.endswith(")"):
                t = t[len(wrapper) + 1 : -1].strip()
        # Array → kembalikan sebagai "array" (ditangani sebagai object)
        if t.startswith("Array("):
            return "array"
        return t.lower()
     
     
    def _cast_df_by_schema(
        df: "pd.DataFrame",
        schema: "pd.DataFrame",
        type_col: str = "_pandas_type",
    ) -> "pd.DataFrame":
        """
        Cast kolom DataFrame berdasarkan dtype target yang sudah disiapkan di skema.
     
        Fungsi ini agnostik terhadap driver — tidak perlu tahu apakah sumber datanya
        ClickHouse atau PostgreSQL. Yang diperlukan hanya kolom ``name`` (nama kolom
        di DataFrame) dan kolom ``type_col`` (dtype Pandas target sebagai string)
        yang sudah disiapkan oleh pemanggil sebelumnya.
     
        Args:
            df:       DataFrame yang akan di-cast.
            schema:   DataFrame hasil DESCRIBE / information_schema yang sudah
                      memiliki kolom ``name`` dan kolom dtype target (``type_col``).
            type_col: Nama kolom di ``schema`` yang berisi dtype Pandas target.
                      Default: ``"_pandas_type"``.
     
        Returns:
            DataFrame baru dengan tipe kolom yang sudah di-cast.
            Kolom yang dtype target-nya None atau tidak dikenal dibiarkan apa adanya.
        """
        
        df = df.copy()
        for _, row in schema.iterrows():
            col_name     = row["name"]
            pandas_dtype = row.get(type_col)
     
            if col_name not in df.columns or pandas_dtype is None:
                continue
     
            try:
                if pandas_dtype == "datetime64[ns]":
                    df[col_name] = pd.to_datetime(df[col_name], errors="coerce")
                elif pandas_dtype in ("bool", "boolean"):
                    df[col_name] = df[col_name].astype("boolean")
                else:
                    df[col_name] = df[col_name].astype(pandas_dtype)
            except (ValueError, TypeError):
                # Tipe tidak bisa di-cast (misal ada nilai korup) — biarkan apa adanya
                console.log(
                    f"[bold yellow]Peringatan:[/] Gagal cast kolom [{col_name}] "
                    f"ke [{pandas_dtype}], dibiarkan sebagai [{df[col_name].dtype}]."
                )
     
        return df
     
     
    def _fetch_typed_sample(nama_table: str, aim: str, sample_rows: int) -> "pd.DataFrame":
        """
        Mengambil sample baris dari tabel source dengan tipe kolom yang akurat.
     
        Masalah utama yang ditangani:
          Kolom bertipe ``Nullable(Int64)`` atau ``Nullable(Float64)`` di ClickHouse,
          serta tipe numerik di PostgreSQL, sering dikembalikan sebagai ``object``
          oleh driver karena Python tidak punya tipe native untuk "int yang bisa None".
          Pandas fallback ke ``object`` untuk menampung campuran nilai dan None,
          sehingga ``generate_table`` tidak bisa menyimpulkan tipe kolom yang benar.
     
        Strategi penanganan per driver:
          - **ClickHouse**: gunakan ``DESCRIBE TABLE`` yang mengembalikan nama dan
            tipe kolom secara eksplisit, lalu cast DataFrame berdasarkan peta
            ``_CH_TO_PANDAS``. ``DESCRIBE TABLE`` adalah perintah native ClickHouse.
          - **PostgreSQL**: gunakan ``information_schema.columns`` yang merupakan
            standar SQL-92 dan tersedia di semua DB relasional (PG, MySQL, MSSQL).
            Cast berdasarkan peta ``_PG_TO_PANDAS``.
          - **Driver lain / fallback**: jika driver tidak dikenal, kembalikan
            DataFrame apa adanya dan tampilkan peringatan.
     
        Untuk semua driver, query data menggunakan ``WHERE col IS NOT NULL AND ...``
        agar baris dengan NULL tidak ikut dalam sample — memperkecil kemungkinan
        driver salah inferensi tipe karena nilai kosong.
     
        Args:
            nama_table:  Nama tabel termasuk schema. Contoh: ``"public.tx_ticket"``,
                         ``"iriis_datainfo.capability_mapping"``.
            aim:         Alias koneksi yang terdaftar di credentials.
            sample_rows: Jumlah baris sample untuk inferensi tipe. Nilai lebih besar
                         lebih aman untuk tabel dengan banyak kolom sparse.
     
        Returns:
            DataFrame dengan dtype kolom yang paling akurat yang bisa diperoleh.
        """
        
        creds = load_credentials(aim)
        driver = creds.get("driver", "").lower()
     
        # --- Langkah 1: ambil skema kolom dari DB ---
        if driver == "clickhouse":
            # DESCRIBE TABLE mengembalikan: name, type, default_type, default_expression, ...
            df_schema = fetch_data(f"DESCRIBE TABLE {nama_table}", aim=aim)
            # Normalisasi nama kolom output DESCRIBE (bisa beda versi CH)
            df_schema = df_schema.rename(columns=lambda c: c.lower())
            df_schema["_pandas_type"] = df_schema["type"].apply(
                lambda t: _CH_TO_PANDAS.get(_parse_ch_type(t))
            )
            type_source = "clickhouse DESCRIBE TABLE"
     
        elif driver == "postgresql":
            # information_schema.columns: standar SQL-92, tersedia di PG / MySQL / MSSQL
            # Pisahkan schema dan table_name dari "schema.table" jika ada
            if "." in nama_table:
                schema_name, table_name = nama_table.split(".", 1)
            else:
                schema_name, table_name = "public", nama_table
     
            df_schema = fetch_data(
                f"SELECT column_name AS name, data_type AS type "
                f"FROM information_schema.columns "
                f"WHERE table_schema = '{schema_name}' "
                f"  AND table_name   = '{table_name}' "
                f"ORDER BY ordinal_position",
                aim=aim,
            )
            df_schema["_pandas_type"] = df_schema["type"].str.lower().map(_PG_TO_PANDAS)
            type_source = "information_schema.columns"
     
        else:
            # Driver tidak dikenal — skip cast, kembalikan data apa adanya
            console.log(
                f"[bold yellow]Peringatan:[/] Driver [{driver}] tidak didukung untuk "
                "inferensi tipe otomatis. DataFrame mungkin bertipe object semua."
            )
            return fetch_data(f"SELECT * FROM {nama_table} LIMIT {sample_rows}", aim=aim)
     
        if df_schema.empty:
            console.log(
                f"[bold yellow]Peringatan:[/] Tidak dapat membaca skema [{nama_table}] "
                f"via {type_source}. Tabel mungkin tidak ada."
            )
            return pd.DataFrame()
        print(df_schema)
        exit()
        # --- Langkah 2: fetch sample dengan filter IS NOT NULL ---
        columns = df_schema["name"].tolist()
        not_null_clause = " AND ".join(f"{col} IS NOT NULL" for col in columns)
        query_filtered = (
            f"SELECT * FROM {nama_table} "
            f"WHERE {not_null_clause} "
            f"LIMIT {sample_rows}"
        )
        df = fetch_data(query_filtered, aim=aim)
        
        if df.empty:
            # Fallback: tabel kosong atau semua baris ada NULL di setidaknya satu kolom
            console.log(
                f"[bold yellow]Peringatan:[/] Sample bersih kosong untuk [{nama_table}]. "
                "Fallback ke query tanpa filter."
            )
            df = fetch_data(f"SELECT * FROM {nama_table} LIMIT {sample_rows}", aim=aim)
     
        if df.empty:
            return df
     
        # --- Langkah 3: cast tipe kolom berdasarkan skema DB ---
        # Kedua driver sudah menyiapkan kolom _pandas_type di df_schema,
        # berisi dtype Pandas target. _cast_df_by_schema membaca kolom itu
        # lalu melakukan cast per kolom secara aman.
        df = _cast_df_by_schema(df, df_schema, type_col="_pandas_type")
     
        return df
    
    
    # --- [1] Ambil sample dari source dengan inferensi tipe yang akurat ---
    console.log(f"[bold cyan]Membaca struktur tabel:[/] {nama_table_source} dari [{aim_source}]")
    df = _fetch_typed_sample(nama_table_source, aim_source, sample_rows)
    
    # --- [2] Resolve driver destination ---
    creds_dest = load_credentials(aim_destination)
    driver_dest = creds_dest.get("driver", "").lower()
 
    # Routing: semua driver yang dikenal dipetakan ke argumen generate_table()
    DRIVER_TABLE_ARG = {
        "clickhouse": "nama_table_ch",
        "postgresql": "nama_table_pg",
    }
 
    if driver_dest not in DRIVER_TABLE_ARG:
        raise ValueError(
            f"Driver destination '{driver_dest}' tidak dikenali. "
            f"Driver yang didukung: {list(DRIVER_TABLE_ARG.keys())}. "
            "Daftarkan driver baru di DRIVER_TABLE_ARG jika diperlukan."
        )
 
    # Bangun keyword arguments untuk generate_table() secara dinamis.
    # Tabel destination diisi sesuai driver, sisanya None.
    # aim_ch / aim_pg juga diisi dengan aim_destination yang sebenarnya
    # agar generate_table tidak connect ke server default yang salah.
    DRIVER_AIM_ARG = {
        "clickhouse": "aim_ch",
        "postgresql": "aim_pg",
    }
 
    table_kwargs = {arg: None for arg in DRIVER_TABLE_ARG.values()}
    table_kwargs[DRIVER_TABLE_ARG[driver_dest]] = nama_table_destination
 
    aim_kwargs = {arg: None for arg in DRIVER_AIM_ARG.values()}
    aim_kwargs[DRIVER_AIM_ARG[driver_dest]] = aim_destination
 
    # --- [3] Buat struktur tabel di destination ---
    console.log(
        f"[bold cyan]Membuat tabel:[/] {nama_table_destination} "
        f"di [{aim_destination}] (driver: {driver_dest}, "
        f"drop_table={drop_table}, with_data={with_data})"
    )
 
    generate_table(
        df,
        **table_kwargs,
        **aim_kwargs,
        drop_table=drop_table,
        ingest_data=with_data,
        **kwargs,
    )
 
    console.log(
        f"[bold green]Selesai![/] Struktur tabel [{nama_table_source}] "
        f"berhasil disalin ke [{nama_table_destination}]."
    )
    return True

    
