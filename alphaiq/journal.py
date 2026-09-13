from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .domain import JournalEvent


@dataclass
class InMemoryJournal:
    events: list[JournalEvent] = field(default_factory=list)

    def append(self, event: JournalEvent) -> None:
        self.events.append(event)


@dataclass
class JsonLinesJournal:
    path: Path

    def append(self, event: JournalEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True, default=str) + "\n")
