"""
Static catalog of upcoming solar and lunar eclipses with high-level visibility
information. Records are sourced from NASA GSFC catalog CSV exports bundled
with the application so lookups stay offline.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class VisibilityWindow:
    """
    Describes where an eclipse can be observed.

    - countries: normalised names that should match user input countries.
    - regions:  sub-national regions (states, provinces) or broader
      geo-labels ("North America") to refine matching.
    - notes:    optional human-readable guidance.
    """

    countries: Sequence[str]
    regions: Sequence[str]
    notes: str = ""

    def normalized_countries(self) -> Iterable[str]:
        for value in self.countries:
            yield value.lower()

    def normalized_regions(self) -> Iterable[str]:
        for value in self.regions:
            yield value.lower()


@dataclass(frozen=True)
class EclipseEvent:
    """
    Represents a single eclipse in the catalog.
    """

    occurs_on: date
    kind: str  # "solar" or "lunar"
    subtype: str  # e.g. "Total", "Annular", "Partial", "Penumbral"
    title: str
    visibility: Sequence[VisibilityWindow]
    peak_description: str

    def __post_init__(self) -> None:
        normalised_kind = self.kind.lower()
        if normalised_kind not in {"solar", "lunar"}:
            raise ValueError(f"Unsupported eclipse kind: {self.kind!r}")


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SOLAR_CSV = "solar_eclipses_1900_2100.csv"
_LUNAR_CSV = "lunar_eclipses_1900_2100.csv"


def _catalog_path(filename: str) -> Path:
    path = _PROJECT_ROOT / filename
    if not path.exists():
        raise FileNotFoundError(f"Catalog file not found: {path}")
    return path


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def _format_coordinate(value: Optional[float], kind: str) -> str:
    if value is None:
        return "unknown"
    hemisphere = ""
    if kind == "lat":
        hemisphere = "N" if value >= 0 else "S"
    elif kind == "lon":
        hemisphere = "E" if value >= 0 else "W"
    return f"{abs(value):.1f}° {hemisphere}"


def _approximate_regions(latitude: Optional[float], longitude: Optional[float]) -> Tuple[str, ...]:
    if latitude is None or longitude is None:
        return ("Global",)

    # normalise longitude to [-180, 180) for simpler comparisons
    lon = ((longitude + 180.0) % 360.0) - 180.0
    lat = latitude

    regions: List[str] = []

    if -170.0 <= lon <= -30.0:
        if lat >= 15.0:
            regions.extend(["North America"])
        elif lat <= -10.0:
            regions.extend(["South America"])
        else:
            regions.extend(["North America", "South America"])
    elif -30.0 < lon <= 60.0:
        if lat >= 35.0:
            regions.extend(["Europe"])
        elif lat >= 0.0:
            regions.extend(["North Africa", "Africa"])
        else:
            regions.extend(["Africa"])
    elif 60.0 < lon <= 120.0:
        if lat >= 25.0:
            regions.extend(["East Asia", "Asia"])
        elif lat >= -10.0:
            regions.extend(["South Asia", "Asia"])
        else:
            regions.extend(["Oceania"])
    else:
        if lat >= 0.0:
            regions.extend(["East Asia", "Asia"])
        else:
            regions.extend(["Oceania"])

    if not regions:
        regions = ["Global"]

    # Preserve order while removing duplicates.
    seen = set()
    ordered = []
    for value in regions:
        normalized = value.lower()
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(value)
    return tuple(ordered)


def _normalise_duration(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    if stripped.startswith("0") and len(stripped) > 1:
        stripped = stripped.lstrip("0")
    return stripped or "0"


def _build_peak_description(
    kind: str,
    magnitude: Optional[str],
    duration: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    saros: Optional[str],
) -> str:
    parts: List[str] = []

    if magnitude:
        eclipse_component = "Sun" if kind == "solar" else "Moon"
        parts.append(f"Magnitude {magnitude} obscuration of the {eclipse_component.lower()}.")

    if duration:
        duration_normalised = _normalise_duration(duration)
        if duration_normalised:
            parts.append(f"Duration around {duration_normalised}.")

    lat_text = _format_coordinate(latitude, "lat")
    lon_text = _format_coordinate(longitude, "lon")
    parts.append(f"Greatest eclipse near {lat_text}, {lon_text}.")

    if saros:
        parts.append(f"Saros cycle {saros}.")

    return " ".join(parts)


def _build_visibility_window(
    latitude: Optional[float],
    longitude: Optional[float],
    saros: Optional[str],
    magnitude: Optional[str],
) -> VisibilityWindow:
    regions = _approximate_regions(latitude, longitude)
    lat_text = _format_coordinate(latitude, "lat")
    lon_text = _format_coordinate(longitude, "lon")
    note_parts = [
        f"Greatest eclipse at {lat_text}, {lon_text}",
    ]
    if magnitude:
        note_parts.append(f"magnitude {magnitude}")
    if saros:
        note_parts.append(f"Saros {saros}")
    notes = "; ".join(note_parts)
    return VisibilityWindow(countries=(), regions=regions, notes=notes)


def _compose_title(occurs_on: date, subtype: str, kind: str) -> str:
    return f"{occurs_on:%B %d, %Y} {subtype} {kind.title()} Eclipse"


def _load_catalog(filename: str, kind: str) -> Tuple[EclipseEvent, ...]:
    path = _catalog_path(filename)
    events: List[EclipseEvent] = []

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                occurs_on = date.fromisoformat(row["Date"])
            except (KeyError, ValueError):
                continue

            subtype = row.get("Type", "").strip().title() or "Unknown"
            saros = row.get("Saros", "").strip() or None
            magnitude_raw = row.get("Magnitude", "")
            magnitude = magnitude_raw.strip() or None
            latitude = _parse_float(row.get("Latitude")) if "Latitude" in row else None
            longitude = _parse_float(row.get("Longitude")) if "Longitude" in row else None
            duration = row.get("Duration", "").strip() or None

            visibility_window = _build_visibility_window(latitude, longitude, saros, magnitude)

            event = EclipseEvent(
                occurs_on=occurs_on,
                kind=kind,
                subtype=subtype,
                title=_compose_title(occurs_on, subtype, kind),
                visibility=(visibility_window,),
                peak_description=_build_peak_description(
                    kind=kind,
                    magnitude=magnitude,
                    duration=duration,
                    latitude=latitude,
                    longitude=longitude,
                    saros=saros,
                ),
            )
            events.append(event)

    return tuple(sorted(events, key=lambda event: event.occurs_on))


@lru_cache(maxsize=None)
def _solar_events() -> Tuple[EclipseEvent, ...]:
    return _load_catalog(_SOLAR_CSV, "solar")


@lru_cache(maxsize=None)
def _lunar_events() -> Tuple[EclipseEvent, ...]:
    return _load_catalog(_LUNAR_CSV, "lunar")


def solar_events() -> Sequence[EclipseEvent]:
    return _solar_events()


def lunar_events() -> Sequence[EclipseEvent]:
    return _lunar_events()


def all_events() -> Sequence[EclipseEvent]:
    return tuple(sorted(_solar_events() + _lunar_events(), key=lambda event: event.occurs_on))
