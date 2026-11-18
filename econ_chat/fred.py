"""FRED data access. Uses FRED's public CSV endpoint (no API key needed),
with a local on-disk cache so the app still works offline."""
from __future__ import annotations
import io, time
from pathlib import Path
import pandas as pd
import requests

SERIES = {
    "GDP": {"name": "Gross Domestic Product", "units": "Billions of USD, SAAR", "freq": "Quarterly"},
    "CPILFESL": {"name": "Core CPI (All Items Less Food & Energy)", "units": "Index 1982-84=100, SA", "freq": "Monthly"},
}
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}"
CACHE = Path(__file__).resolve().parent.parent / "data"
MAX_AGE = 6 * 3600


def load(series_id: str, refresh: bool = False) -> pd.Series:
    series_id = series_id.upper()
    if series_id not in SERIES:
        raise ValueError(f"Unknown series {series_id}; choose from {list(SERIES)}")
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{series_id}.csv"
    fresh = f.exists() and time.time() - f.stat().st_mtime < MAX_AGE
    if refresh or not fresh:
        try:
            r = requests.get(URL.format(id=series_id), timeout=20)
            r.raise_for_status()
            f.write_text(r.text)
        except requests.RequestException:
            if not f.exists():
                raise
    df = pd.read_csv(io.StringIO(f.read_text()), parse_dates=[0], na_values=["."])
    s = df.set_index(df.columns[0])[series_id].dropna().astype(float)
    s.index.name = "date"
    s.name = series_id
    return s
