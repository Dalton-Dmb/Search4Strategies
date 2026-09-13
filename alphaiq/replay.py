from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Sequence

from .domain import MarketSnapshot


@dataclass(frozen=True)
class ReplayStep:
    as_of: datetime
    history: tuple[MarketSnapshot, ...]


class DeterministicReplay:
    """Point-in-time replay that only exposes observations available at each step."""

    def __init__(self, snapshots: Sequence[MarketSnapshot]) -> None:
        ordered = tuple(sorted(snapshots, key=lambda x: x.timestamp))
        for earlier, later in zip(ordered, ordered[1:]):
            if later.timestamp < earlier.timestamp:
                raise ValueError("snapshots must be sortable by timestamp")
        self._snapshots = ordered

    def steps(self) -> Iterator[ReplayStep]:
        history: list[MarketSnapshot] = []
        for snapshot in self._snapshots:
            history.append(snapshot)
            yield ReplayStep(as_of=snapshot.timestamp, history=tuple(history))

    def signature(self) -> tuple[tuple[str, str, str, float], ...]:
        return tuple(
            (
                item.symbol,
                item.timeframe,
                item.timestamp.isoformat(),
                item.close,
            )
            for item in self._snapshots
        )
