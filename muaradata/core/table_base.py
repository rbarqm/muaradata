from abc import ABC, abstractmethod

class BaseTableGenerator(ABC):
    def __init__(self, client):
        self.client = client

    @abstractmethod
    def generate(self, df, table_name, drop_table=True, **kwargs):
        pass
