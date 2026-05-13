from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class PresenceState(Enum):
    ALIVE = "ALIVE"
    SUSPECTED = "SUSPECTED"
    DEAD = "DEAD"


@dataclass
class PresenceEntry:
    user_id: str
    last_heartbeat: float
    state: PresenceState
    suspected_at: float | None = None


class PresenceManager:
    HEARTBEAT_INTERVAL_S = 5.0
    SUSPECT_AFTER_MISSED = 3
    DEAD_AFTER_SUSPECT_S = 15.0

    def __init__(self, on_state_change: Callable[[str, str], None], time_fn=None):
        self._members = {}
        self._on_state_change = on_state_change
        self._time_fn = time_fn or time.time

    def register_member(self, user_id: str):
        self._members[user_id] = PresenceEntry(
            user_id=user_id,
            last_heartbeat=self._time_fn(),
            state=PresenceState.ALIVE,
        )

    def unregister_member(self, user_id: str):
        self._members.pop(user_id, None)

    def record_heartbeat(self, user_id: str):
        entry = self._members.get(user_id)
        if not entry:
            return

        entry.last_heartbeat = self._time_fn()

        if entry.state == PresenceState.SUSPECTED:
            entry.state = PresenceState.ALIVE
            entry.suspected_at = None
            self._on_state_change(user_id, "reconnected")

    def check_liveness(self):
        now = self._time_fn()
        suspect_threshold = self.HEARTBEAT_INTERVAL_S * self.SUSPECT_AFTER_MISSED

        for uid, entry in list(self._members.items()):
            elapsed = now - entry.last_heartbeat

            if entry.state == PresenceState.ALIVE:
                if elapsed > suspect_threshold:
                    entry.state = PresenceState.SUSPECTED
                    entry.suspected_at = now
                    self._on_state_change(uid, "suspected")

            elif entry.state == PresenceState.SUSPECTED:
                if entry.suspected_at and (now - entry.suspected_at > self.DEAD_AFTER_SUSPECT_S):
                    entry.state = PresenceState.DEAD
                    self._on_state_change(uid, "timeout")

    def get_member_presence(self, user_id: str):
        return self._members.get(user_id)
