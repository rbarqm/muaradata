from ..drivers.clickhouse.clickhouse_table import ClickHouseTableGenerator
from ..drivers.postgresql.postgresql_table import PostgresTableGenerator
from ..drivers.mysql.mysql_table import MySQLTableGenerator

TABLE_REGISTRY = {
    "clickhouse": ClickHouseTableGenerator,
    "postgresql": PostgresTableGenerator,
    "mysql": MySQLTableGenerator,
}
