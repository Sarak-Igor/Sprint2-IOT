from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    async def connect(self): pass

    @abstractmethod
    async def publish(self, payload: str): pass

    @abstractmethod
    async def start_loop(self): pass
