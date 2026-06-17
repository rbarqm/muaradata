from .tcp import ClickHouseTCPClient
from .http import ClickHouseHTTPClient

class ClickHouseDriver:
    def __init__(self, creds, tunnels):
        self.creds = creds
        self.tunnels = tunnels
        self.client = None

    def connect(self):
        method = self.creds.get("methode", 1)
        
        if method == 'Clickhouse HTTP':
            self.client = ClickHouseHTTPClient(self.creds).connect()
        else:            
            self.client = ClickHouseTCPClient(self.creds, self.tunnels).connect()

        return self

    def query(self, sql):
        return self.client.query(sql)

    def execute(self, sql):
        self.client.execute(sql)
    
    def insert_dataframe(self, df, table, columns):
        self.client.insert_dataframe(df, table, columns)