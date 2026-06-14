from abc import ABC, abstractmethod

class BaseInserter(ABC):
    def __init__(self, client):
        self.client = client

    @abstractmethod
    def insert(self, df, table, columns, truncate=False):
        pass
