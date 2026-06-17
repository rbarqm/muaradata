from ..drivers.clickhouse.driver import ClickHouseDriver
from ..drivers.postgresql.driver import PostgresDB
from ..drivers.mysql.driver import MySQLConnector

REGISTRY = {
    "clickhouse": ClickHouseDriver,
    "postgresql": PostgresDB,
    "mysql": MySQLConnector,
}
