import logging
import sys
from typing import Any, Dict, Optional, Set

import posthog

logger = logging.getLogger(__name__)

import os
import uuid
from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict


class ServerContext(Enum):
    NONE = "None"
    FASTAPI = "FastAPI"


class ProductTelemetryEvent:
    max_batch_size: ClassVar[int] = 1
    batch_size: int

    def __init__(self, batch_size: int = 1):
        self.batch_size = batch_size

    @property
    def properties(self) -> Dict[str, Any]:
        return self.__dict__

    @property
    def name(self) -> str:
        return self.__class__.__name__

    # A batch key is used to determine whether two events can be batched together.
    # If a TelemetryEvent's max_batch_size > 1, batch_key() and batch() MUST be
    # implemented.
    # Otherwise they are ignored.
    @property
    def batch_key(self) -> str:
        return self.name

    def batch(self, other: "ProductTelemetryEvent") -> "ProductTelemetryEvent":
        raise NotImplementedError


class SessionStartEvent(ProductTelemetryEvent):
    session_name: str

    def __init__(self, session_name: str):
        super().__init__()
        self.session_name = session_name


class SessionEventEvent(ProductTelemetryEvent):
    event_type: str
    message: Optional[str]

    def __init__(self, event_type: str, message: Optional[str] = None):
        super().__init__()
        self.event_type = event_type
        self.message = message


class ProductTelemetryClient:
    USER_ID_PATH = str(Path.home() / ".cache" / "devon" / "telemetry_user_id")
    UNKNOWN_USER_ID = "UNKNOWN"
    SERVER_CONTEXT: ServerContext = ServerContext.FASTAPI
    _curr_user_id = None

    @abstractmethod
    def capture(self, event: ProductTelemetryEvent) -> None:
        pass

    @property
    def context(self) -> Dict[str, Any]:
        telemetry_settings = {}

        self._context = {
            "server_context": self.SERVER_CONTEXT.value,
            **telemetry_settings,
        }
        return self._context

    @property
    def user_id(self) -> str:
        if self._curr_user_id:
            return self._curr_user_id

        # File access may fail due to permissions or other reasons. We don't want to
        # crash so we catch all exceptions.
        try:
            if not os.path.exists(self.USER_ID_PATH):
                os.makedirs(os.path.dirname(self.USER_ID_PATH), exist_ok=True)
                with open(self.USER_ID_PATH, "w") as f:
                    new_user_id = str(uuid.uuid4())
                    f.write(new_user_id)
                self._curr_user_id = new_user_id
            else:
                with open(self.USER_ID_PATH, "r") as f:
                    self._curr_user_id = f.read()
        except Exception:
            self._curr_user_id = self.UNKNOWN_USER_ID
        return self._curr_user_id


class Posthog(ProductTelemetryClient):
    def __init__(self):
        telemetry_disabled = os.getenv("DEVON_TELEMETRY_DISABLED")
        if telemetry_disabled == "true":
            posthog.disabled = True

        posthog.project_api_key = "phc_odaedyRgd1jAk3qnlUBWj4o3v5xeJiGeyLTgXPA7dAx"
        # posthog_logger = logging.getLogger("posthog")
        # Silence posthog's logging
        # posthog_logger.disabled = True

        self.batched_events: Dict[str, ProductTelemetryEvent] = {}
        self.seen_event_types: Set[Any] = set()

        super().__init__()

    def capture(self, event: ProductTelemetryEvent) -> None:
        if event.max_batch_size == 1 or event.batch_key not in self.seen_event_types:
            self.seen_event_types.add(event.batch_key)
            self._direct_capture(event)
            return
        batch_key = event.batch_key
        if batch_key not in self.batched_events:
            self.batched_events[batch_key] = event
            return
        batched_event = self.batched_events[batch_key].batch(event)
        self.batched_events[batch_key] = batched_event
        if batched_event.batch_size >= batched_event.max_batch_size:
            self._direct_capture(batched_event)
            del self.batched_events[batch_key]

    def _direct_capture(self, event: ProductTelemetryEvent) -> None:
        try:
            # print(event.name)
            result = posthog.capture(
                self.user_id,
                event.name,
                {**event.properties, **self.context},
            )
            print(result)
        except Exception as e:
            logger.error(f"Failed to send telemetry event {event.name}: {e}")
