from iriis_connection_library.core.table_base import BaseTableGenerator
from iriis_connection_library.core.dtype import pandas_dtypes

MAPPING_CH = {
    'OBJECT': 'String',
    'FLOAT64': 'Float64',
    'FLOAT32': 'Float32',
    'INT64': 'Int64',
    'INT32': 'Int32',
    'INT16': 'Int16',
    'INT8': 'Int8',
    'DATETIME64[NS]': 'DateTime',
    'DATETIME64[D]': 'Date',
    'BOOL': 'UInt8',
}

class ClickHouseTableGenerator(BaseTableGenerator):

    def generate(self, df, table_name, drop_table=True, store_in_disk2=True):
        dtypes, df = pandas_dtypes(df)
        fields = []

        for col, dtype in dtypes.items():
            ch_type = MAPPING_CH.get(dtype, 'String')
            fields.append(f"`{col}` Nullable({ch_type})")

        fields.append("`updated_at` Nullable(DateTime) DEFAULT now()")
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {", ".join(fields)}
        )
        ENGINE = MergeTree()
        ORDER BY tuple()
        """

        if store_in_disk2:
            ddl += " SETTINGS storage_policy='move_from_default_to_disk_1'"

        if drop_table:
            self.client.execute(f"DROP TABLE IF EXISTS {table_name}")

        self.client.execute(ddl)
        return True
