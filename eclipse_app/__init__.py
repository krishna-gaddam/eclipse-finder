"""
Public package interface for `eclipse_app`.

Re-exports the primary data structures and helper functions used by the app so
callers can import them directly from `eclipse_app`.
"""

from .eclipse_data import (
    EclipseEvent,
    VisibilityWindow,
    all_events,
    lunar_events,
    solar_events,
)
from .eclipse_matcher import (
    event_summary,
    find_next_eclipses,
    is_visible_from,
    matching_window,
    next_visible_event,
)
from .location_resolver import (
    LocationQuery,
    normalize_country,
    normalize_region,
    parse_location_input,
)

__all__ = [
    "EclipseEvent",
    "VisibilityWindow",
    "all_events",
    "lunar_events",
    "solar_events",
    "event_summary",
    "find_next_eclipses",
    "is_visible_from",
    "matching_window",
    "next_visible_event",
    "LocationQuery",
    "normalize_country",
    "normalize_region",
    "parse_location_input",
]
