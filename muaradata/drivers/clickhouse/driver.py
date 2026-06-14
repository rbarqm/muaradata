from iriis_connection_library.drivers.clickhouse.tcp import ClickHouseTCPClient
from iriis_connection_library.drivers.clickhouse.http import ClickHouseHTTPClient

class ClickHouseDriver:
    def __init__(self, creds, tunnels):
        self.creds = creds
        self.tunnels = tunnels
        self.client = None

    def connect(self):
        method = self.creds.get("methode", 1)
        
        if method == 3:
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