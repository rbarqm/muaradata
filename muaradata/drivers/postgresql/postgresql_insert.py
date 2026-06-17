from ...core.insert_base import BaseInserter
from time import sleep

class PostgresInserter:

    def __init__(self, driver):
        self.driver = driver

    def insert(self, df, table, columns, truncate=False):
        if truncate:
            print(f"Clear Out {table}")
            self.driver.execute(f"TRUNCATE TABLE {table}")
            sleep(10)

        self.driver.insert_dataframe(df, table, columns)