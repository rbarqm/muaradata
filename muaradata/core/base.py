from abc import ABC, abstractmethod

class BaseDB(ABC):
    def __init__(self, creds: dict):
        self.creds = creds
        self.engine = None

    @abstractmethod
    def connect(self, exec=False):
        pass

    @abstractmethod
    def query(self, sql):
        pass

    @abstractmethod
    def execute(self, sql):
        pass
