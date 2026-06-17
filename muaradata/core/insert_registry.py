from ..drivers.clickhouse.clickhouse_insert import ClickHouseInserter
from ..drivers.postgresql.postgresql_insert import PostgresInserter
from ..drivers.mysql.mysql_insert import MySQLInserter

INSERT_REGISTRY = {
    "clickhouse": ClickHouseInserter,
    "postgresql": PostgresInserter,
    "mysql": MySQLInserter,
}
