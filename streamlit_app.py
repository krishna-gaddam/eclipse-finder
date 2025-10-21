from __future__ import annotations

from datetime import date
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eclipse_app import eclipse_matcher
from eclipse_app.location_resolver import LocationQuery, parse_location_input


EVENT_CARD_CSS = """
<style>
.event-card {
    position: relative;
    border-radius: 18px;
    padding: 1.6rem;
    color: #f5f9ff;
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.35);
    overflow: hidden;
}
.event-card:before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    pointer-events: none;
}
.event-card--solar {
    background: linear-gradient(140deg, #ff9a44, #ff6126, #ef3b36);
}
.event-card--solar:before {
    background: radial-gradient(circle at top right, rgba(255, 244, 214, 0.45), transparent 55%);
}
.event-card--lunar {
    background: linear-gradient(140deg, #f0f4f8, #c7ccd3, #a6abb4);
    color: #1d2636;
}
.event-card--lunar:before {
    background: radial-gradient(circle at top right, rgba(255,255,255,0.6), transparent 55%);
}
.event-card--lunar .event-card__heading,
.event-card--lunar .event-card__meta span:first-child {
    color: rgba(48, 60, 78, 0.72);
}
.event-card--lunar .event-card__description {
    color: rgba(32, 43, 65, 0.9);
}
.event-card--lunar .event-card__note {
    background: rgba(255, 255, 255, 0.65);
    color: rgba(32, 43, 65, 0.85);
}
.event-card__heading {
    font-size: 0.85rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(221, 230, 255, 0.78);
    margin-bottom: 0.4rem;
}
.event-card__title {
    font-size: 1.4rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
}
.event-card__tags {
    margin-bottom: 1rem;
}
.event-card__tag {
    display: inline-block;
    padding: 0.25rem 0.9rem;
    margin-right: 0.4rem;
    border-radius: 999px;
    background: rgba(15, 76, 129, 0.6);
    font-size: 0.82rem;
    font-weight: 500;
}
.event-card--solar .event-card__tag {
    background: rgba(255, 255, 255, 0.28);
}
.event-card--lunar .event-card__tag {
    background: rgba(42, 55, 80, 0.75);
    color: #eef3ff;
}
.event-card__meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.95rem;
    margin-bottom: 0.35rem;
}
.event-card__meta span:first-child {
    color: rgba(220, 230, 255, 0.8);
    text-transform: uppercase;
    font-size: 0.78rem;
    letter-spacing: 0.1em;
}
.event-card__description {
    margin-top: 1rem;
    line-height: 1.55;
    font-size: 0.96rem;
    color: rgba(235, 242, 255, 0.92);
}
.event-card__note {
    margin-top: 0.75rem;
    padding: 0.6rem 0.85rem;
    border-radius: 12px;
    background: rgba(12, 48, 84, 0.6);
    font-size: 0.9rem;
    color: rgba(233, 241, 255, 0.9);
}
</style>
"""


def _render_event_card(
    event, location: LocationQuery, heading: str, reference_date: date
) -> None:
    days_until = (event.occurs_on - reference_date).days
    countdown_label = "Days until"
    if days_until >= 0:
        countdown_value = f"{days_until} day{'s' if days_until != 1 else ''}"
    else:
        countdown_label = "Occurred"
        countdown_value = f"{abs(days_until)} day{'s' if abs(days_until) != 1 else ''} ago"
    window = eclipse_matcher.matching_window(event, location)
    visibility_note = ""
    if window:
        if window.notes:
            visibility_note = window.notes
        elif window.regions:
            regions = ", ".join(sorted(set(window.regions)))
            visibility_note = f"Regions: {regions}"

    card_class = "event-card event-card--solar" if event.kind.lower() == "solar" else "event-card event-card--lunar"
    card_html = f"""
    <div class="{card_class}">
        <div class="event-card__heading">{heading}</div>
        <div class="event-card__title">{event.title}</div>
        <div class="event-card__tags">
            <span class="event-card__tag">{event.subtype} {event.kind.title()}</span>
        </div>
        <div class="event-card__meta"><span>Date</span><span>{event.occurs_on:%B %d, %Y}</span></div>
        <div class="event-card__meta"><span>{countdown_label}</span><span>{countdown_value}</span></div>
        <div class="event-card__description">{event.peak_description}</div>
        {'<div class="event-card__note"><strong>Visibility:</strong> ' + visibility_note + '</div>' if visibility_note else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def _render_no_match(kind: str) -> None:
    st.warning(
        f"No upcoming {kind} eclipses in the current catalog match this location. "
        "Try broadening the location (for example, provide only the state or country)."
    )


def main() -> None:
    st.set_page_config(page_title="Eclipse Finder", layout="centered")
    st.markdown(EVENT_CARD_CSS, unsafe_allow_html=True)

    st.sidebar.title("Catalog Overview")
    st.sidebar.markdown(
        "- Offline NASA GSFC eclipse catalog (1900-2100)\n"
        "- Visibility hints generated from greatest-eclipse coordinates\n"
        "- Filtered using your location, postal code, or region keywords"
    )
    st.sidebar.subheader("Tips")
    st.sidebar.markdown(
        "- Check nearby states or provinces if your city is missing\n"
        "- Adjust the reference date to explore future years\n"
        "- Try entering only a country for broad coverage"
    )
    st.sidebar.caption("Data refresh: restart Streamlit after updating the CSV files.")

    st.title("Eclipse Finder")
    st.write(
        "Discover the next solar and lunar eclipses that should be visible from your location. "
        "Enter a city/state/country combination or a supported postal code."
    )

    with st.form("location-form"):
        location_input = st.text_input(
            "Location",
            placeholder="Austin, TX, USA or 78701",
            help="Use 'City, State, Country' or provide a ZIP/postal code (US ZIP and Canadian postal supported).",
        )
        reference_date = st.date_input(
            "Reference date",
            value=date.today(),
            help="Forecast from this date forward. Defaults to today.",
        )
        submitted = st.form_submit_button("Find eclipses")

    if not submitted:
        st.info("Submit the form to see upcoming eclipses.")
        return

    location_input = location_input.strip()
    if not location_input:
        st.error("Please provide a location.")
        return

    try:
        location = parse_location_input(location_input)
    except ValueError as exc:
        st.error(str(exc))
        return

    if not any([location.city, location.region, location.country, location.postal_code]):
        st.error("Could not interpret the provided location. Try including a country name.")
        return

    display_location = location.formatted() or location.raw
    st.success(f"Searching eclipse catalog for: {display_location}")

    solar, lunar = eclipse_matcher.find_next_eclipses(location, reference_date)

    solar_col, lunar_col = st.columns(2)
    with solar_col:
        if solar:
            _render_event_card(solar, location, "Next Solar Eclipse", reference_date)
        else:
            _render_no_match("solar")

    with lunar_col:
        if lunar:
            _render_event_card(lunar, location, "Next Lunar Eclipse", reference_date)
        else:
            _render_no_match("lunar")


if __name__ == "__main__":
    main()
