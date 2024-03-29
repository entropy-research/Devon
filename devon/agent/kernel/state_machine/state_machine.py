from typing import Dict
from .state_types import StateType
from .state import State

class StateMachine:
    def __init__(self, initial_state: StateType):
        self.state: StateType = initial_state
        self.states: Dict[StateType, State] = {}

    def add_state(self, state_type: StateType, state: State):
        self.states[state_type] = state

    def transition(self, state_type: StateType, context):
        self.state = state_type
        self.states[state_type].execute(context)

    def run(self, context):
        while self.state != "terminate":
            self.transition(self.state, context)

    def get_state(self) -> StateType:
        return self.state

    def set_state(self, state_type: StateType):
        self.state = state_type
