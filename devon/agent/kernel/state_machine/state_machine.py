from abc import ABC, abstractmethod

from devon.agent.kernel.state_machine.state_types import State

class State(ABC):

    @abstractmethod
    def execute(self, input):
        pass

class StateMachine:

    def __init__(self):
        self.state_dict = {}

    def add_state(self, name: State, function):
        self.state_dict[name] = function
    
    def execute_state(self, name, input):
        self.state_dict[name](input=input)