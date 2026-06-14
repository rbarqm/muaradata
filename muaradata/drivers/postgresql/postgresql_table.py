from iriis_connection_library.core.table_base import BaseTableGenerator
from iriis_connection_library.core.dtype import pandas_dtypes

MAPPING_PG = {
    'OBJECT': 'TEXT',
    'FLOAT64': 'DOUBLE PRECISION',
    'FLOAT32': 'DOUBLE PRECISION',
    'INT64': 'BIGINT',
    'INT32': 'BIGINT',
    'INT16': 'BIGINT',
    'INT8': 'BIGINT',
    'DATETIME64[NS]': 'TIMESTAMP',
    'BOOL': 'BOOLEAN',
}

class PostgresTableGenerator(BaseTableGenerator):

    def generate(self, df, table_name, drop_table=True, store_in_disk2=False):
        dtypes, df = pandas_dtypes(df)
        fields = []
        
        for col, dtype in dtypes.items():
            pg_type = MAPPING_PG.get(dtype.upper(), 'TEXT')            
            fields.append(f"\"{col}\" {pg_type}")
        
        fields.append("created_at TIMESTAMP DEFAULT NOW()")
        
        ddl = f"""
        CREATE TABLE {table_name} (
            {", ".join(fields)}
        )
        """
        
        if drop_table:
            self.client.execute(f"DROP TABLE IF EXISTS {table_name}")

        self.client.execute(ddl)        
        
        return True
