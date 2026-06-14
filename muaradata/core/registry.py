from iriis_connection_library.drivers.clickhouse.driver import ClickHouseDriver
from iriis_connection_library.drivers.postgresql.driver import PostgresDB
from iriis_connection_library.drivers.mysql.driver import MySQLConnector

REGISTRY = {
    "clickhouse": ClickHouseDriver,
    "postgresql": PostgresDB,
    "mysql": MySQLConnector,
}
