from abc import ABC, abstractmethod

class BaseCHClient(ABC):
    def __init__(self, creds):
        self.creds = creds

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def query(self, sql):
        pass

    @abstractmethod
    def execute(self, sql):
        pass
    
    @abstractmethod
    def insert_dataframe(self, df, table, columns):
        pass
    