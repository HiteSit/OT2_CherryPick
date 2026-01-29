from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Sequence, Union

SourceStream = Literal["stdout", "stderr"]


@dataclass(frozen=True)
class LabwareLoadEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_slot: str
    well: Optional[str] = None
    volume_ul: Optional[float] = None
    rate_ul_s: Optional[float] = None


@dataclass(frozen=True)
class TipPickupEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_slot: str
    well: Optional[str]
    volume_ul: Optional[float] = None
    rate_ul_s: Optional[float] = None


@dataclass(frozen=True)
class TipDropEvent:
    sequence_index: int
    source: SourceStream
    labware_display: Optional[str]
    labware_slot: str
    well: Optional[str]
    volume_ul: Optional[float] = None
    rate_ul_s: Optional[float] = None


@dataclass(frozen=True)
class AspirateEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_slot: str
    well: str
    volume_ul: float
    rate_ul_s: float


@dataclass(frozen=True)
class DispenseEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_slot: str
    well: str
    volume_ul: float
    rate_ul_s: float


@dataclass(frozen=True)
class MixEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_slot: str
    well: Optional[str]
    volume_ul: Optional[float]
    rate_ul_s: Optional[float] = None


RawEvent = Union[
    LabwareLoadEvent,
    TipPickupEvent,
    TipDropEvent,
    AspirateEvent,
    DispenseEvent,
    MixEvent,
]


@dataclass(frozen=True)
class ParseWarning:
    line: int
    reason: str


@dataclass(frozen=True)
class ParseResult:
    events: Sequence[RawEvent]
    warnings: Sequence[ParseWarning]
