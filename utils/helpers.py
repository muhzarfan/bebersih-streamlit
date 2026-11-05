"""Shared helper functions."""
import re
import warnings

import pandas as pd


def is_text_dtype(s: pd.Series) -> bool:
    """True for object / string columns (works for pandas 2 and 3)."""
    return pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)


def is_numeric(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)


def parse_dates(s: pd.Series, dayfirst: bool = False) -> pd.Series:
    """Parse many date formats; unparseable values become NaT (never raises)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return pd.to_datetime(s, errors="coerce", format="mixed", dayfirst=dayfirst)
        except (TypeError, ValueError):
            return pd.to_datetime(s, errors="coerce", dayfirst=dayfirst)


def date_shape(value: str) -> str:
    """Replace digits with 9 and letters with a to compare date layouts."""
    return re.sub(r"[A-Za-z]", "a", re.sub(r"\d", "9", str(value).strip()))


def fmt_int(n) -> str:
    return f"{int(n):,}"


def pct(part, whole) -> float:
    return round(100.0 * part / whole, 2) if whole else 0.0
