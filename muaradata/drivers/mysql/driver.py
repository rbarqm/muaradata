import pandas as pd
import numpy as np
import mysql.connector
from sshtunnel import SSHTunnelForwarder
from rich.console import Console
from iriis_connection_library.core.pool import ConnectionPool

console = Console(log_path=False)

class MySQLConnector:
    
    def __init__(self, creds, tunnels):
        self.creds = creds
        self.tunnels = tunnels
        self.conn = None
        self.pool = ConnectionPool(self.connect)
    
    def connect(self):
        host = self.creds["host"]
        port = self.creds["port"]
        jumper = self.creds["use_tunnel"]
        
        if jumper:
            host_tunnel=self.tunnels["host_tunnel"]
            user_tunnel=self.tunnels["user_tunnel"]
            pass_tunnel=self.tunnels["pass_tunnel"]
            
            self.tunnel = SSHTunnelForwarder(
                (host_tunnel, 22),
                ssh_username=user_tunnel,
                ssh_password=pass_tunnel,
                remote_bind_address=(host, port)
            )
            
            self.tunnel.start()

            self.conn = mysql.connector.connect(
                host=host,
                user=self.creds["username"],
                password=self.creds["password"],
                database=self.creds["database"]
            )
        
        else:
            self.conn = mysql.connector.connect(
                host=host,
                user=self.creds["username"],
                password=self.creds["password"],
                database=self.creds["database"]
            )
        
        return self
    
    def query(self, sql):
        return pd.read_sql_query(sql, self.conn)
    
    def execute(self, sql):
        with self.conn.cursor() as cur:
            cur.execute(sql)
        self.conn.commit()
    
    def insert_dataframe(self, df, table, columns):
        IGNORE = {"", np.nan, None, np.inf, -np.inf, 'nan', 'NaN', 'no_need', 'No Need', 'None'}

        actual_columns = [col for col in columns if col in df.columns]
        if not actual_columns:
            actual_columns = list(df.columns)
            
        values = [tuple(None if pd.isna(x) or x in IGNORE else x for x in row) for row in df[actual_columns].to_numpy()]    
        
        col_list = ", ".join([f"`{c}`" for c in actual_columns])
        
        placeholders = ", ".join(["%s"] * len(actual_columns))
        
        with console.status(f"[bold green]INSERTING DATA {table}") as status:
            sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
            
            with self.conn.cursor() as cur:
                cur.executemany(sql, values)
            
            self.conn.commit()
            console.log("Data Saved Successfully!")
