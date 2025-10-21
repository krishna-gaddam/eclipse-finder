"""
Logic for matching eclipse events to a user's location and extracting the next
visible solar and lunar eclipses.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Sequence, Tuple

from . import eclipse_data
from .eclipse_data import EclipseEvent, VisibilityWindow
from .location_resolver import LocationQuery


def _window_matches_location(window: VisibilityWindow, location: LocationQuery) -> bool:
    location_tokens = location.tokens()

    country_tokens = {country.lower() for country in window.countries}
    region_tokens = {region.lower() for region in window.regions}

    # Country match is optional if the window omits countries, otherwise ensure overlap.
    if country_tokens:
        if location.country:
            if location.country.lower() not in country_tokens and not (
                location_tokens & country_tokens
            ):
                return False
        else:
            # No explicit country supplied by the user, rely on regional tokens.
            if not (location_tokens & country_tokens):
                return False

    if not region_tokens:
        return True

    if location.region:
        region_lower = location.region.lower()
        if region_lower in region_tokens:
            return True
    # Check for overlap with broader macro-region tokens.
    if location_tokens & region_tokens:
        return True

    # If the user did not provide a region but country matches, treat as visible.
    if location.region is None and country_tokens:
        if location.country and location.country.lower() in country_tokens:
            return True

    return False


def is_visible_from(event: EclipseEvent, location: LocationQuery) -> bool:
    for window in event.visibility:
        if _window_matches_location(window, location):
            return True
    return False


def matching_window(
    event: EclipseEvent, location: LocationQuery
) -> Optional[VisibilityWindow]:
    for window in event.visibility:
        if _window_matches_location(window, location):
            return window
    return None


def next_visible_event(
    events: Sequence[EclipseEvent],
    location: LocationQuery,
    start_date: Optional[date] = None,
) -> Optional[EclipseEvent]:
    reference_date = start_date or date.today()
    for event in events:
        if event.occurs_on < reference_date:
            continue
        if is_visible_from(event, location):
            return event
    return None


def find_next_eclipses(
    location: LocationQuery, reference_date: Optional[date] = None
) -> Tuple[Optional[EclipseEvent], Optional[EclipseEvent]]:
    solar = next_visible_event(eclipse_data.solar_events(), location, reference_date)
    lunar = next_visible_event(eclipse_data.lunar_events(), location, reference_date)
    return solar, lunar


def event_summary(event: EclipseEvent) -> str:
    return f"{event.occurs_on.isoformat()} - {event.subtype} {event.kind.title()} - {event.title}"
