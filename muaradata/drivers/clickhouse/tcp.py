import warnings
warnings.filterwarnings('ignore')
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from clickhouse_driver import Client
from rich.console import Console
from iriis_connection_library.drivers.clickhouse.client_base import BaseCHClient

console = Console(log_path=False)

class ClickHouseTCPClient(BaseCHClient):
    def __init__(self, creds, tunnels=None):
        self.creds = creds
        self.tunnels = tunnels
        self.client = None
        self.tunnel = None
    
    def connect(self):
        
        host = self.creds["host"]
        port = self.creds["port"]
        
        jumper = self.creds["use_tunnel"]
        jumper = False if pd.isna(jumper) else bool(jumper)
        
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

            self.client = Client(
                host='127.0.0.1',
                port=self.tunnel.local_bind_port,
                user=self.creds["username"],
                password=self.creds["password"],
                settings={"use_numpy": True},
            )
        
        else:
            self.client = Client(
                host=host,
                user=self.creds["username"],
                password=self.creds["password"],
                settings={"use_numpy": True},
            )
        
        return self

    def query(self, sql):
        return self.client.query_dataframe(sql)

    def execute(self, sql):
        self.client.execute(sql)
    
    def insert_dataframe(self, data, table, columns):
        sql = f"""
        INSERT INTO {table} ({columns})
        VALUES
        """
        
        with console.status(f"[bold green]INSERTING DATA {table}") as status:
            self.client.execute(
                sql,
                data,
                types_check=True,
                columnar=True
            )
            console.log("Data Saved Successfully!")