from abc import ABC, abstractmethod

class Source(ABC):
    name = "base"
    @abstractmethod
    def versions(self): raise NotImplementedError
    def details(self, version): return version.raw
