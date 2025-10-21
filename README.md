# Eclipse Finder

Offline-first eclipse planner that helps you surface the next solar and lunar eclipses visible from any supported location. It ships with a NASA GSFC catalog covering 1900-2100, so lookups work instantly without network access and can be reused from the CLI or Streamlit UI.

## Features

- Works entirely offline using the bundled `solar_eclipses_1900_2100.csv` and `lunar_eclipses_1900_2100.csv` catalogs (see `catalog_key.csv` for column descriptions).
- Flexible location parsing: accepts free-form city/state/country strings, U.S. ZIP codes, Canadian postal codes, and macro-region keywords.
- Visibility hints pull in notes and regional tags so you know why an event matches your location.
- CLI and Streamlit experiences share the same matcher logic, ensuring consistent answers across interfaces.
- Styled Streamlit cards surface countdowns, peak descriptions, and visibility notes at a glance.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.9+ is recommended. If you already have an environment, you only need to `pip install streamlit==1.50.0`.

## Command-Line Usage

Run the CLI without arguments to be prompted for a location:

```bash
python3 app.py
```

You can also supply arguments directly:

```bash
python3 app.py --location "Toronto, ON, Canada"
python3 app.py --location "78701" --reference-date 2026-08-01
```

Key flags:

- `--location` / `-l`: `City, State/Province, Country` strings or supported postal codes.
- `--reference-date` / `-d`: Forecast from a different date (`YYYY-MM-DD`). Leave empty to use today.

The CLI prints summaries for the next solar and lunar events along with peak details. If nothing matches, you'll receive suggestions for broadening the search.

## Streamlit App

Launch the interactive UI:

```bash
streamlit run streamlit_app.py
```

- Enter a location and optional reference date, then submit the form to render twin cards for the next solar and lunar eclipses.
- The sidebar highlights catalog provenance and tips for tweaking searches.
- Each card shows countdowns, peak descriptions, and visibility notes derived from the same logic used in the CLI.
- Restart Streamlit after replacing the CSV catalogs so fresh data loads.

## Project Layout

- `app.py`: Command-line interface wiring argument parsing, location resolution, and event summaries.
- `streamlit_app.py`: Streamlit front end with custom styling and card rendering helpers.
- `eclipse_app/eclipse_data.py`: Loads catalog CSVs, builds rich event records, and crafts human-readable peak descriptions.
- `eclipse_app/location_resolver.py`: Normalises free-form locations, infers regions from postal codes, and generates matching tokens.
- `eclipse_app/eclipse_matcher.py`: Matches events against the parsed location and finds the next visible solar and lunar eclipses.

## Updating the Catalog

Replace the CSVs with updated NASA GSFC exports (or your own data following the existing schema). Ensure the files live alongside the code, keep column names consistent with `catalog_key.csv`, and restart any running Streamlit session to reload the data.

## Limitations

- Visibility windows are approximations derived from greatest-eclipse coordinates and macro-regional heuristics rather than precise path polygons.
- Postal code resolution is coarse: U.S. ZIP support aggregates by 3-digit prefixes, and Canadian postal codes map to provinces using the first letter.
- If you do not see a local match, try searching with only a state/province and country or use broader regional keywords (`"North America"`, `"Europe"`, etc.).
