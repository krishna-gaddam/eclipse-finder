from __future__ import annotations

import argparse
from datetime import date
from typing import Optional

from eclipse_app import eclipse_matcher
from eclipse_app.location_resolver import LocationQuery, parse_location_input


def _parse_reference_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        year, month, day = (int(part) for part in value.split("-"))
        return date(year, month, day)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Expected YYYY-MM-DD for reference date, got {value!r}"
        ) from exc


def describe_event(event, location: LocationQuery) -> str:
    window = eclipse_matcher.matching_window(event, location)
    lines = [
        eclipse_matcher.event_summary(event),
        f"    Peak details: {event.peak_description}",
    ]
    if window and window.notes:
        lines.append(f"    Visibility note: {window.notes}")
    elif window and window.regions:
        lines.append(
            "    Visibility regions: "
            + ", ".join(sorted(set(window.regions)))
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover the next solar and lunar eclipses visible from your location."
    )
    parser.add_argument(
        "-l",
        "--location",
        help="Location as 'City, State, Country' or a ZIP/postal code. If omitted you will be prompted.",
    )
    parser.add_argument(
        "-d",
        "--reference-date",
        type=_parse_reference_date,
        help="Override today's date (YYYY-MM-DD) for forecasting in the future.",
    )
    args = parser.parse_args()

    reference_date = args.reference_date

    if args.location:
        location_input = args.location
    else:
        try:
            location_input = input(
                "Enter city, state, country (e.g. 'Austin, TX, USA') or postal code: "
            )
        except EOFError:
            raise SystemExit("No location provided.")

    try:
        location = parse_location_input(location_input)
    except ValueError as exc:
        raise SystemExit(str(exc))

    if not any([location.city, location.region, location.country, location.postal_code]):
        raise SystemExit("Could not interpret the provided location.")

    print(f"Searching eclipse catalog for: {location.formatted() or location.raw}")

    solar, lunar = eclipse_matcher.find_next_eclipses(location, reference_date)

    if solar:
        print("\nNext solar eclipse:")
        print(describe_event(solar, location))
    else:
        print("\nNo upcoming solar eclipses match your location in the current catalog.")

    if lunar:
        print("\nNext lunar eclipse:")
        print(describe_event(lunar, location))
    else:
        print("\nNo upcoming lunar eclipses match your location in the current catalog.")

    if not (solar and lunar):
        print(
            "\nTip: try expanding your search (e.g. provide only state and country) "
            "if your exact location is not covered."
        )


if __name__ == "__main__":
    main()
