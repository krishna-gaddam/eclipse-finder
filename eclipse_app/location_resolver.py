"""
Utilities to parse loosely formatted user location input and normalise it into a
structured representation that can be matched against eclipse visibility
windows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Sequence, Set, Tuple

# ---------------------------------------------------------------------------
# Canonical country list and aliases
# ---------------------------------------------------------------------------

_COUNTRY_CANONICAL = {
    "united states": "United States",
    "united states of america": "United States",
    "usa": "United States",
    "us": "United States",
    "canada": "Canada",
    "mexico": "Mexico",
    "spain": "Spain",
    "france": "France",
    "united kingdom": "United Kingdom",
    "uk": "United Kingdom",
    "great britain": "United Kingdom",
    "ireland": "Ireland",
    "portugal": "Portugal",
    "brazil": "Brazil",
    "argentina": "Argentina",
    "chile": "Chile",
    "peru": "Peru",
    "greenland": "Greenland",
    "iceland": "Iceland",
    "morocco": "Morocco",
    "algeria": "Algeria",
    "libya": "Libya",
    "egypt": "Egypt",
    "saudi arabia": "Saudi Arabia",
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "oman": "Oman",
    "yemen": "Yemen",
    "india": "India",
    "bangladesh": "Bangladesh",
    "china": "China",
    "japan": "Japan",
    "south korea": "South Korea",
    "korea": "South Korea",
    "pakistan": "Pakistan",
    "nigeria": "Nigeria",
    "kenya": "Kenya",
    "south africa": "South Africa",
    "germany": "Germany",
    "italy": "Italy",
    "tunisia": "Tunisia",
    "new zealand": "New Zealand",
    "australia": "Australia",
}


# Countries grouped into broader geographic tokens for fuzzy matching
_COUNTRY_MACROREGIONS = {
    "United States": {"north america"},
    "Canada": {"north america"},
    "Mexico": {"north america"},
    "Greenland": {"north america", "arctic"},
    "Iceland": {"europe", "north atlantic"},
    "Spain": {"europe"},
    "France": {"europe"},
    "United Kingdom": {"europe"},
    "Ireland": {"europe"},
    "Portugal": {"europe"},
    "Germany": {"europe"},
    "Italy": {"europe"},
    "Morocco": {"africa", "north africa"},
    "Algeria": {"africa", "north africa"},
    "Libya": {"africa", "north africa"},
    "Tunisia": {"africa", "north africa"},
    "Egypt": {"africa", "north africa", "middle east"},
    "Saudi Arabia": {"asia", "middle east"},
    "United Arab Emirates": {"asia", "middle east"},
    "Oman": {"asia", "middle east"},
    "Yemen": {"asia", "middle east"},
    "India": {"asia", "south asia"},
    "Bangladesh": {"asia", "south asia"},
    "Pakistan": {"asia", "south asia"},
    "China": {"asia", "east asia"},
    "Japan": {"asia", "east asia"},
    "South Korea": {"asia", "east asia"},
    "Kenya": {"africa", "east africa"},
    "Nigeria": {"africa", "west africa"},
    "South Africa": {"africa"},
    "Brazil": {"south america"},
    "Argentina": {"south america"},
    "Chile": {"south america"},
    "Australia": {"oceania"},
    "New Zealand": {"oceania"},
}


# ---------------------------------------------------------------------------
# Regions, states, and provinces with aliases
# ---------------------------------------------------------------------------

_US_STATES = (
    ("Alabama", "AL"),
    ("Alaska", "AK"),
    ("Arizona", "AZ"),
    ("Arkansas", "AR"),
    ("California", "CA"),
    ("Colorado", "CO"),
    ("Connecticut", "CT"),
    ("Delaware", "DE"),
    ("District of Columbia", "DC"),
    ("Florida", "FL"),
    ("Georgia", "GA"),
    ("Hawaii", "HI"),
    ("Idaho", "ID"),
    ("Illinois", "IL"),
    ("Indiana", "IN"),
    ("Iowa", "IA"),
    ("Kansas", "KS"),
    ("Kentucky", "KY"),
    ("Louisiana", "LA"),
    ("Maine", "ME"),
    ("Maryland", "MD"),
    ("Massachusetts", "MA"),
    ("Michigan", "MI"),
    ("Minnesota", "MN"),
    ("Mississippi", "MS"),
    ("Missouri", "MO"),
    ("Montana", "MT"),
    ("Nebraska", "NE"),
    ("Nevada", "NV"),
    ("New Hampshire", "NH"),
    ("New Jersey", "NJ"),
    ("New Mexico", "NM"),
    ("New York", "NY"),
    ("North Carolina", "NC"),
    ("North Dakota", "ND"),
    ("Ohio", "OH"),
    ("Oklahoma", "OK"),
    ("Oregon", "OR"),
    ("Pennsylvania", "PA"),
    ("Rhode Island", "RI"),
    ("South Carolina", "SC"),
    ("South Dakota", "SD"),
    ("Tennessee", "TN"),
    ("Texas", "TX"),
    ("Utah", "UT"),
    ("Vermont", "VT"),
    ("Virginia", "VA"),
    ("Washington", "WA"),
    ("West Virginia", "WV"),
    ("Wisconsin", "WI"),
    ("Wyoming", "WY"),
    ("Puerto Rico", "PR"),
)

_CANADA_PROVINCES = (
    ("Alberta", "AB"),
    ("British Columbia", "BC"),
    ("Manitoba", "MB"),
    ("New Brunswick", "NB"),
    ("Newfoundland and Labrador", "NL"),
    ("Northwest Territories", "NT"),
    ("Nova Scotia", "NS"),
    ("Nunavut", "NU"),
    ("Ontario", "ON"),
    ("Prince Edward Island", "PE"),
    ("Quebec", "QC"),
    ("Saskatchewan", "SK"),
    ("Yukon", "YT"),
)

_MEXICO_STATES = (
    ("Sinaloa", "SIN"),
    ("Coahuila", "COA"),
    ("Nuevo Leon", "NLE"),
    ("Durango", "DUR"),
)

_SPAIN_REGIONS = (
    ("Galicia", ""),
    ("Asturias", ""),
    ("Castile and Leon", ""),
    ("Basque Country", ""),
    ("Navarre", ""),
    ("Aragon", ""),
    ("Catalonia", ""),
)

_AUSTRALIA_STATES = (
    ("New South Wales", "NSW"),
    ("Queensland", "QLD"),
    ("Northern Territory", "NT"),
    ("Western Australia", "WA"),
    ("Victoria", "VIC"),
    ("South Australia", "SA"),
    ("Tasmania", "TAS"),
)

_NEW_ZEALAND_REGIONS = (
    ("North Island", ""),
    ("South Island", ""),
    ("Southland", ""),
    ("Otago", ""),
)


def _build_region_aliases() -> Dict[str, Tuple[str, Optional[str]]]:
    result: Dict[str, Tuple[str, Optional[str]]] = {}

    def add(entries: Sequence[Tuple[str, str]], country: Optional[str]) -> None:
        for name, abbr in entries:
            key = name.lower()
            result[key] = (name, country)
            if abbr:
                result[abbr.lower()] = (name, country)

    add(_US_STATES, "United States")
    add(_CANADA_PROVINCES, "Canada")
    add(_MEXICO_STATES, "Mexico")
    add(_SPAIN_REGIONS, "Spain")
    add(_AUSTRALIA_STATES, "Australia")
    add(_NEW_ZEALAND_REGIONS, "New Zealand")

    # Additional region-level aliases that are useful for matching
    result["north america"] = ("North America", None)
    result["south america"] = ("South America", None)
    result["central america"] = ("Central America", None)
    result["europe"] = ("Europe", None)
    result["western europe"] = ("Western Europe", None)
    result["eastern europe"] = ("Eastern Europe", None)
    result["africa"] = ("Africa", None)
    result["north africa"] = ("North Africa", None)
    result["east africa"] = ("East Africa", None)
    result["west africa"] = ("West Africa", None)
    result["middle east"] = ("Middle East", None)
    result["south asia"] = ("South Asia", None)
    result["east asia"] = ("East Asia", None)
    result["oceania"] = ("Oceania", None)
    result["arctic"] = ("Arctic", None)

    return result


_REGION_ALIAS_LOOKUP = _build_region_aliases()


# ---------------------------------------------------------------------------
# Postal code resolution (limited to U.S. ZIP codes and Canadian postal codes)
# ---------------------------------------------------------------------------

_ZIP_STATE_RANGES: Sequence[Tuple[int, int, str]] = (
    (5, 9, "Puerto Rico"),
    (10, 27, "Massachusetts"),
    (28, 29, "Rhode Island"),
    (30, 38, "New Hampshire"),
    (39, 49, "Maine"),
    (50, 59, "Vermont"),
    (60, 69, "Connecticut"),
    (70, 89, "New Jersey"),
    (90, 98, "Armed Forces Europe"),
    (100, 149, "New York"),
    (150, 196, "Pennsylvania"),
    (197, 199, "Delaware"),
    (200, 205, "District of Columbia"),
    (206, 219, "Maryland"),
    (220, 246, "Virginia"),
    (247, 268, "West Virginia"),
    (270, 289, "North Carolina"),
    (290, 299, "South Carolina"),
    (300, 319, "Georgia"),
    (320, 349, "Florida"),
    (350, 369, "Alabama"),
    (370, 385, "Tennessee"),
    (386, 397, "Mississippi"),
    (398, 399, "Georgia"),
    (400, 427, "Kentucky"),
    (430, 459, "Ohio"),
    (460, 479, "Indiana"),
    (480, 499, "Michigan"),
    (500, 528, "Iowa"),
    (530, 549, "Wisconsin"),
    (550, 567, "Minnesota"),
    (570, 577, "South Dakota"),
    (580, 588, "North Dakota"),
    (590, 599, "Montana"),
    (600, 629, "Illinois"),
    (630, 658, "Missouri"),
    (660, 679, "Kansas"),
    (680, 693, "Nebraska"),
    (700, 715, "Louisiana"),
    (716, 729, "Arkansas"),
    (730, 749, "Oklahoma"),
    (750, 799, "Texas"),
    (800, 816, "Colorado"),
    (820, 831, "Wyoming"),
    (832, 838, "Idaho"),
    (840, 847, "Utah"),
    (850, 865, "Arizona"),
    (870, 884, "New Mexico"),
    (889, 898, "Nevada"),
    (900, 961, "California"),
    (962, 966, "Armed Forces Pacific"),
    (967, 968, "Hawaii"),
    (970, 979, "Oregon"),
    (980, 994, "Washington"),
    (995, 999, "Alaska"),
)

_CANADA_POSTAL_PREFIX = {
    "A": "Newfoundland and Labrador",
    "B": "Nova Scotia",
    "C": "Prince Edward Island",
    "E": "New Brunswick",
    "G": "Quebec",
    "H": "Quebec",
    "J": "Quebec",
    "K": "Ontario",
    "L": "Ontario",
    "M": "Ontario",
    "N": "Ontario",
    "P": "Ontario",
    "R": "Manitoba",
    "S": "Saskatchewan",
    "T": "Alberta",
    "V": "British Columbia",
    "X": "Nunavut",
    "Y": "Yukon",
}


def _resolve_us_zip(zip_code: str) -> Optional[Tuple[str, str]]:
    digits = re.sub(r"\D", "", zip_code)
    if len(digits) < 3:
        return None
    try:
        prefix = int(digits[:3])
    except ValueError:
        return None
    for lower, upper, state in _ZIP_STATE_RANGES:
        if lower <= prefix <= upper:
            country = "United States" if state not in {"Armed Forces Europe", "Armed Forces Pacific"} else "United States"
            if state.startswith("Armed Forces"):
                state = state
            return state, country
    return None


def _resolve_canadian_postal(code: str) -> Optional[Tuple[str, str]]:
    cleaned = code.replace(" ", "").upper()
    if len(cleaned) < 1:
        return None
    first = cleaned[0]
    province = _CANADA_POSTAL_PREFIX.get(first)
    if province:
        return province, "Canada"
    return None


def resolve_postal_code(code: str) -> Optional[Tuple[str, str]]:
    """
    Attempt to derive (region, country) from a postal code. Currently supports:
    - United States ZIP codes (3-digit prefix mapping)
    - Canadian postal codes (first-letter mapping)
    """

    code = code.strip()
    if not code:
        return None

    # U.S. ZIP codes are numeric (optionally with a hyphen)
    if re.fullmatch(r"\d{5}(-\d{4})?", code):
        return _resolve_us_zip(code)

    # Canadian postal codes follow the A1A 1A1 pattern
    if re.fullmatch(r"[A-Za-z]\d[A-Za-z](?:\s?\d[A-Za-z]\d)?", code):
        return _resolve_canadian_postal(code)

    return None


# ---------------------------------------------------------------------------
# Location parsing
# ---------------------------------------------------------------------------


def _normalise_token(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


@dataclass
class LocationQuery:
    raw: str
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    def tokens(self) -> Set[str]:
        result: Set[str] = set()
        if self.city:
            result.update(word.lower() for word in self.city.split())
            result.add(self.city.lower())
        if self.region:
            result.add(self.region.lower())
            result.update(word.lower() for word in self.region.split())
        if self.country:
            result.add(self.country.lower())
            for alias, canonical in _COUNTRY_CANONICAL.items():
                if canonical == self.country:
                    result.add(alias)
            result.update(_COUNTRY_MACROREGIONS.get(self.country, set()))
        return result

    def formatted(self) -> str:
        components = [self.city, self.region, self.country]
        return ", ".join(component for component in components if component)


def parse_location_input(user_input: str) -> LocationQuery:
    """
    Parse a free-form location string into structured components. The parser is
    intentionally forgiving and is aimed at matching the eclipse catalog rather
    than providing precise geocoding.
    """

    raw = user_input.strip()
    if not raw:
        raise ValueError("Location input cannot be empty.")

    # Postal code shortcut
    if re.fullmatch(r"\d{5}(?:-\d{4})?", raw) or re.fullmatch(r"[A-Za-z]\d[A-Za-z](?:\s?\d[A-Za-z]\d)?", raw):
        lookup = resolve_postal_code(raw)
        region, country = (lookup if lookup else (None, None))
        return LocationQuery(raw=user_input, region=region, country=country, postal_code=raw)

    components = [component.strip() for component in raw.split(",") if component.strip()]
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

    for component in reversed(components):
        token = _normalise_token(component)
        if not country:
            country_candidate = _COUNTRY_CANONICAL.get(token)
            if country_candidate:
                country = country_candidate
                continue
        if not region:
            region_candidate = _REGION_ALIAS_LOOKUP.get(token)
            if region_candidate:
                region, inferred_country = region_candidate
                if inferred_country and not country:
                    country = inferred_country
                continue
        if not city:
            city = component.strip()
        else:
            city = f"{component.strip()} {city}"

    if not city and components:
        city = components[0].strip()

    # Fallback: try to peel off a trailing state/province abbreviation from the city
    if city:
        trailing_match = re.search(r"\b([A-Za-z]{2})$", city)
        if trailing_match and not region:
            candidate = trailing_match.group(1).lower()
            region_candidate = _REGION_ALIAS_LOOKUP.get(candidate)
            if region_candidate:
                region, inferred_country = region_candidate
                city = city[: trailing_match.start()].strip(", ").strip() or None
                if inferred_country and not country:
                    country = inferred_country

    if region and not country:
        # Try to infer a country from the region mapping.
        region_token = region.lower()
        region_candidate = _REGION_ALIAS_LOOKUP.get(region_token)
        if region_candidate:
            _, inferred_country = region_candidate
            if inferred_country:
                country = inferred_country

    if city:
        city = city.strip() or None

    if city and region and city.lower() == region.lower():
        city = None

    if city and country and city.lower() == country.lower():
        city = None

    country = normalize_country(country)
    region = normalize_region(region)

    return LocationQuery(raw=user_input, city=city, region=region, country=country, postal_code=None)


def normalize_country(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    token = _normalise_token(name)
    return _COUNTRY_CANONICAL.get(token, name.strip())


def normalize_region(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    token = _normalise_token(name)
    region_candidate = _REGION_ALIAS_LOOKUP.get(token)
    if region_candidate:
        return region_candidate[0]
    return name.strip()


def location_matches_visibility(
    location: LocationQuery, visibility: Sequence[Tuple[str, Sequence[str]]]
) -> bool:
    """
    Deprecated helper retained for backwards compatibility.
    """

    raise NotImplementedError("Use match_visibility_window from eclipse_matcher instead.")
