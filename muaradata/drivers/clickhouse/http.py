import os
import pandas as pd
import clickhouse_connect
from rich.console import Console
from .client_base import BaseCHClient

console = Console(log_path=False)

class ClickHouseHTTPClient(BaseCHClient):
    
    def __init__(self, creds, tunnels=None):
        self.creds = creds
        self.tunnels = tunnels
        self.client = None
        self.tunnel = None
    
    def connect(self):
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        os.environ.pop("http_proxy", None)
        os.environ.pop("https_proxy", None)
        os.environ["NO_PROXY"] = "localhost, 127.0.0.1"
        
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

            self.client = clickhouse_connect.get_client(
                host='127.0.0.1', #self.creds["host"],
                port=self.tunnel.local_bind_port,
                username=self.creds["username"],
                password=self.creds["password"],
                secure=True,
                verify=False
            )
        
        else:
            self.client = clickhouse_connect.get_client(
                host=self.creds["host"],
                port=self.creds.get("port", 9443),
                username=self.creds["username"],
                password=self.creds["password"],
                secure=True,
                verify=False
            )
        
        return self

    def query(self, sql):
        result = self.client.query(sql)
        df = pd.DataFrame(result.result_rows, columns=result.column_names)
        return df

    def execute(self, sql):
        self.client.command(sql)
    
    def insert_dataframe(self, df, table, columns):
        with console.status(f"[bold green]INSERTING DATA {table}") as status:
            self.client.insert_df(
                table=table,
                df=df[columns]
            )
            console.log("Data Saved Successfully!")