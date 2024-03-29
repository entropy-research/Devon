from abc import ABC, abstractmethod

class State(ABC):

    @abstractmethod
    def execute(self, context):
        pass
