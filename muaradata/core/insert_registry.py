from iriis_connection_library.drivers.clickhouse.clickhouse_insert import ClickHouseInserter
from iriis_connection_library.drivers.postgresql.postgresql_insert import PostgresInserter
from iriis_connection_library.drivers.mysql.mysql_insert import MySQLInserter

INSERT_REGISTRY = {
    "clickhouse": ClickHouseInserter,
    "postgresql": PostgresInserter,
    "mysql": MySQLInserter,
}
