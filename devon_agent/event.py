from abc import ABC
from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal, Optional, TypedDict


class Event(TypedDict):
    type: str
    content: Any
    producer: str
    consumer: str
    trajectory_id: str
    metadata: Dict[str, Any]
    timestamp: Optional[str]


# decorator for wrapping functions that add events for call and return
def eventifyResult(event_type: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            event = Event(
                type=event_type,
                content=func(*args, **kwargs),
                producer=func.__name__,
                consumer=func.__module__,
                metadata={},
                timestamp=None,
            )
            return event

        return wrapper

    return decorator


class EventLoop(ABC):
    def __init__(self):
        self.events: list[Event] = []

    def add_event(self, event: Event):
        self.events.append(event)

    def get_events(self):
        return self.events

    def clear_events(self):
        self.events = []

    def run(self):
        pass

    def suscribe(self, event_type: str, callback: Callable):
        pass

    def unsuscribe(self, event_type: str, callback: Callable):
        pass
