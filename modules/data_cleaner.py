"""Cleaning operations. Every function returns new objects; inputs are never modified."""
import re

import numpy as np
import pandas as pd

from modules import outlier_detector as od
from utils.helpers import is_numeric, is_text_dtype, parse_dates

METHODS = ["No action", "Drop rows", "Mean", "Median", "Mode", "Custom value"]
_METHOD_KEY = {"No action": "none", "Drop rows": "drop_rows", "Mean": "mean",
               "Median": "median", "Mode": "mode", "Custom value": "custom"}


def method_key(label: str) -> str:
    return _METHOD_KEY.get(label, "none")


def _entry(op, col, affected, detail, level="info"):
    return {"operation": op, "column": col, "affected": int(affected), "detail": detail, "level": level}


def _changed(a: pd.Series, b: pd.Series) -> int:
    same = (a == b) | (a.isna() & b.isna())
    return int((~same.fillna(False)).sum())


def default_config() -> dict:
    return {"text": {}, "types": {}, "dates": {}, "duplicates": {"enabled": False},
            "missing": {}, "outliers": {}, "rename": {}, "replace": {}, "drop_columns": []}


# ---------------------------------------------------------------- missing values
def handle_missing(df, rules: dict):
    out, log = df.copy(), []
    for col, rule in rules.items():
        method = rule.get("method", "none")
        if method == "none" or col not in out.columns:
            continue
        n_miss = int(out[col].isna().sum())
        if n_miss == 0:
            continue
        if method == "drop_rows":
            out = out[out[col].notna()]
            log.append(_entry("Missing Values: Drop Rows", col, n_miss, f"Dropped {n_miss} row(s)"))
            continue
        if method in ("mean", "median"):
            if not is_numeric(out[col]):
                log.append(_entry("Missing Values", col, 0,
                                  f"{method.title()} imputation skipped: column is not numeric.", "warning"))
                continue
            val = out[col].mean() if method == "mean" else out[col].median()
            if pd.api.types.is_integer_dtype(out[col]):
                val = int(round(val))
        elif method == "mode":
            modes = out[col].mode(dropna=True)
            if modes.empty:
                log.append(_entry("Missing Values", col, 0, "Mode imputation skipped: no values.", "warning"))
                continue
            val = modes.iloc[0]
        elif method == "custom":
            val = rule.get("value", "")
            if is_numeric(out[col]):
                try:
                    val = float(val)
                    if pd.api.types.is_integer_dtype(out[col]) and val.is_integer():
                        val = int(val)
                except (TypeError, ValueError):
                    log.append(_entry("Missing Values", col, 0,
                                      "Custom value skipped: it is not numeric.", "warning"))
                    continue
        else:
            continue
        try:
            out[col] = out[col].fillna(val)
        except (TypeError, ValueError) as e:
            log.append(_entry("Missing Values", col, 0, f"Fill failed: {e}", "warning"))
            continue
        log.append(_entry(f"Missing Values: {method.title()} Imputation", col, n_miss,
                          f"Filled {n_miss} value(s) with {val!r}"))
    return out, log


# ---------------------------------------------------------------- duplicates
def remove_duplicates(df, subset=None, keep="first"):
    subset = [c for c in (subset or []) if c in df.columns] or None
    mask = df.duplicated(subset=subset, keep=keep)
    n = int(mask.sum())
    scope = ", ".join(subset) if subset else "all columns"
    return df.loc[~mask].copy(), [_entry("Remove Duplicates", scope, n,
                                         f"Removed {n} duplicate row(s), keeping {keep} occurrence")]


# ---------------------------------------------------------------- text
def clean_text(df, columns, strip=True, collapse=True, case="none"):
    """`case` is either one mode for all columns or a {column: mode} dict.
    Modes: none, lower, upper, title."""
    out, log = df.copy(), []
    for c in columns:
        if c not in out.columns or not is_text_dtype(out[c]):
            continue
        before = out[c]
        col_case = case.get(c, "none") if isinstance(case, dict) else case

        def f(v):
            if not isinstance(v, str):
                return v
            if collapse:
                v = " ".join(v.split()) if strip else re.sub(r"\s{2,}", " ", v)
            elif strip:
                v = v.strip()
            return {"lower": v.lower, "upper": v.upper, "title": v.title}.get(col_case, lambda: v)()

        out[c] = before.map(f)
        n = _changed(before, out[c])
        if n:
            log.append(_entry("Text Cleaning", c, n, f"Standardised {n} value(s) "
                              f"(strip={strip}, collapse spaces={collapse}, case={col_case})"))
    return out, log


# ---------------------------------------------------------------- types
def convert_type(s: pd.Series, target: str):
    """Return (converted series or None if refused, message, level)."""
    na_before = int(s.isna().sum())
    if target == "String":
        return s.map(lambda v: v if pd.isna(v) else str(v)), "Converted to string", "info"
    if target == "Datetime":
        res = parse_dates(s)
    else:
        num = pd.to_numeric(s, errors="coerce")
        if target == "Integer":
            valid = num.dropna()
            if (valid % 1 != 0).any():
                return None, "Conversion to Integer refused: column contains decimal values.", "warning"
            res = num.astype("Int64")
        else:
            res = num.astype(float)
    new_na = int(res.isna().sum()) - na_before
    if new_na > 0:
        return res, f"Converted to {target}; {new_na} value(s) could not be converted and became missing", "warning"
    return res, f"Converted to {target} without data loss", "info"


def convert_types(df, mapping: dict):
    out, log = df.copy(), []
    for c, target in mapping.items():
        if c not in out.columns or target in (None, "No change"):
            continue
        res, msg, level = convert_type(out[c], target)
        if res is None:
            log.append(_entry("Type Conversion", c, 0, msg, level))
            continue
        old = str(out[c].dtype)
        out[c] = res
        log.append(_entry("Type Conversion", c, len(out), f"{old} -> {res.dtype}. {msg}", level))
    return out, log


# ---------------------------------------------------------------- dates
def clean_dates(df, columns, out_format="%Y-%m-%d", dayfirst=False):
    out, log = df.copy(), []
    for c in columns:
        if c not in out.columns:
            continue
        parsed = parse_dates(out[c], dayfirst=dayfirst)
        invalid = int((parsed.isna() & out[c].notna()).sum())
        out[c] = parsed.dt.strftime(out_format).where(parsed.notna(), np.nan)
        log.append(_entry("Date Cleaning", c, int(parsed.notna().sum()),
                          f"Formatted as {out_format}; {invalid} invalid date(s) set to missing",
                          "warning" if invalid else "info"))
    return out, log

# ---------------------------------------------------------------- drop columns
def drop_columns(df, columns):
    """Remove columns. Refuses to remove every column."""
    cols = [c for c in (columns or []) if c in df.columns]
    if not cols:
        return df.copy(), []
    if len(cols) >= df.shape[1]:
        return df.copy(), [_entry("Drop Columns", ", ".join(map(str, cols)), 0,
                                  "Skipped: this would remove every column.", "warning")]
    log = [_entry("Drop Columns", c, int(df[c].notna().sum()),
                  f"Dropped column ({int(df[c].notna().sum())} non-missing value(s) removed)") for c in cols]
    return df.drop(columns=cols), log

# ---------------------------------------------------------------- rename / replace
def rename_columns(df, mapping: dict):
    """Rename columns. Empty names and names that already exist are skipped with a warning."""
    out, log = df.copy(), []
    names = set(out.columns)
    for old, new in mapping.items():
        new = str(new).strip()
        if old not in names or not new or new == old:
            continue
        if new in names:
            log.append(_entry("Rename Column", old, 0, f"Skipped: a column named '{new}' already exists.", "warning"))
            continue
        out = out.rename(columns={old: new})
        names.discard(old)
        names.add(new)
        log.append(_entry("Rename Column", old, 1, f"'{old}' -> '{new}'"))
    return out, log


def replace_values(df, rules: dict):
    """rules = {column: {old_value: new_value}}. Exact match on text values; NaN is never touched."""
    out, log = df.copy(), []
    for col, mapping in rules.items():
        if col not in out.columns or not mapping:
            continue
        if not is_text_dtype(out[col]):
            log.append(_entry("Replace Values", col, 0, "Skipped: column is not text.", "warning"))
            continue
        before = out[col]
        out[col] = before.map(lambda v: mapping.get(v, v) if isinstance(v, str) else v)
        n = _changed(before, out[col])
        log.append(_entry("Replace Values", col, n, f"{len(mapping)} replacement rule(s) applied; {n} cell(s) changed"))
    return out, log


# ---------------------------------------------------------------- pipeline
def run_pipeline(df: pd.DataFrame, config: dict):
    """Apply configured operations in a fixed, reproducible order.
    Order: drop columns -> replace values -> text -> dates -> types -> duplicates -> missing -> outliers -> rename.
    Dropped columns are removed first, so settings that mention them are ignored and duplicates are detected on
    the remaining columns. Rename runs last so every other setting can keep using the original column names."""
    out, log = df.copy(), []
    if config.get("replace"):
        out, l = replace_values(out, config["replace"])
        log += l
    t = config.get("text") or {}
    if t.get("columns"):
        out, l = clean_text(out, t["columns"], t.get("strip", True), t.get("collapse", True), t.get("case", "none"))
        log += l
    d = config.get("dates") or {}
    if d.get("columns"):
        out, l = clean_dates(out, d["columns"], d.get("format", "%Y-%m-%d"), d.get("dayfirst", False))
        log += l
    if config.get("types"):
        out, l = convert_types(out, config["types"])
        log += l
    dup = config.get("duplicates") or {}
    if dup.get("enabled"):
        out, l = remove_duplicates(out, dup.get("subset"), dup.get("keep", "first"))
        log += l
    if config.get("missing"):
        out, l = handle_missing(out, config["missing"])
        log += l
    if config.get("outliers"):
        out, l = od.treat(out, config["outliers"])
        log += l
    if config.get("rename"):
        out, l = rename_columns(out, config["rename"])
        log += l
    return out, log