"""Data quality analysis: missing, duplicates, types, inconsistencies, statistics."""
import numpy as np
import pandas as pd

from utils.helpers import TIME_ONLY, date_shape, is_numeric, is_text_dtype, parse_dates, pct


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    miss = df.isna().sum()
    out = pd.DataFrame({"Column": df.columns, "Missing Count": miss.values,
                        "Missing %": [pct(m, len(df)) for m in miss.values]})
    return out.sort_values("Missing Count", ascending=False, ignore_index=True)


def duplicate_summary(df: pd.DataFrame) -> dict:
    mask = df.duplicated(keep="first")
    return {"count": int(mask.sum()), "percent": pct(mask.sum(), len(df)),
            "rows": df[df.duplicated(keep=False)]}


def _ratio(series_ok: pd.Series, n: int) -> float:
    return float(series_ok.sum()) / n if n else 0.0


def dtype_analysis(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in df.columns:
        s = df[c]
        nn = s.dropna()
        suggestion, note = "-", ""
        if len(nn) == 0:
            note = "Empty column"
        elif is_text_dtype(s):
            txt = nn.astype(str).str.strip()
            if _ratio(pd.to_numeric(txt, errors="coerce").notna(), len(txt)) >= 0.9:
                suggestion, note = "Numeric", "Text values that look numeric"
            elif txt.map(lambda v: bool(TIME_ONLY.match(v))).mean() >= 0.9:
                suggestion, note = "Time", "Text values that look like times (no date)"
            elif _ratio(parse_dates(txt).notna(), len(txt)) >= 0.9:
                suggestion, note = "Datetime", "Text values that look like dates"
            if nn.map(type).nunique() > 1:
                note = (note + "; " if note else "") + "Mixed Python types"
        rows.append({"Column": c, "Current Type": str(s.dtype), "Non-Null": int(len(nn)),
                     "Unique": int(nn.nunique()), "Suggested Type": suggestion,
                     "Notes": note or "OK"})
    return pd.DataFrame(rows)


def inconsistency_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in df.columns:
        s = df[c]
        if not is_text_dtype(s):
            continue
        txt = s.dropna()
        txt = txt[txt.map(lambda v: isinstance(v, str))]
        if txt.empty:
            continue
        ws = int((txt != txt.str.strip()).sum())
        if ws:
            rows.append({"Column": c, "Issue": "Leading/trailing whitespace", "Affected": ws,
                         "Example": repr(txt[txt != txt.str.strip()].iloc[0])})
        multi = int(txt.str.contains(r"\s{2,}").sum())
        if multi:
            rows.append({"Column": c, "Issue": "Repeated internal spaces", "Affected": multi,
                         "Example": repr(txt[txt.str.contains(r"\s{2,}")].iloc[0])})
        norm = txt.str.strip().str.lower()
        variants = txt.str.strip().groupby(norm).nunique()
        bad = variants[variants > 1]
        if len(bad):
            ex = sorted(txt.str.strip()[norm == bad.index[0]].unique())[:4]
            rows.append({"Column": c, "Issue": "Capitalisation variants", "Affected": int(bad.sum()),
                         "Example": ", ".join(map(str, ex))})
        stripped = txt.str.strip()
        if stripped.nunique() > 1 and _ratio(parse_dates(stripped).notna(), len(stripped)) >= 0.8:
            shapes = stripped.map(date_shape).value_counts()
            if len(shapes) > 1:
                rows.append({"Column": c, "Issue": "Mixed date formats", "Affected": int(shapes.iloc[1:].sum()),
                             "Example": ", ".join(shapes.index[:3])})
    return pd.DataFrame(rows, columns=["Column", "Issue", "Affected", "Example"])


def numeric_stats(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in df.columns:
        if is_numeric(df[c]) and df[c].notna().any():
            v = df[c].astype(float)
            rows.append({"Column": c, "Mean": v.mean(), "Median": v.median(),
                         "Std Dev": v.std(), "Min": v.min(), "Max": v.max()})
    return pd.DataFrame(rows, columns=["Column", "Mean", "Median", "Std Dev", "Min", "Max"])


def categorical_stats(df: pd.DataFrame, top: int = 5) -> pd.DataFrame:
    rows = []
    for c in df.columns:
        if is_numeric(df[c]) or pd.api.types.is_datetime64_any_dtype(df[c]):
            continue
        vc = df[c].dropna().astype(str).value_counts()
        if vc.empty:
            continue
        rows.append({"Column": c, "Unique Values": int(len(vc)),
                     "Most Frequent": ", ".join(f"{k} ({v})" for k, v in vc.head(top).items())})
    return pd.DataFrame(rows, columns=["Column", "Unique Values", "Most Frequent"])


def quality_score(df: pd.DataFrame) -> dict:
    """Transparent score = average of three components (each 0-100):
    Completeness = 100 * (1 - missing cells / total cells)
    Uniqueness   = 100 * (1 - duplicate rows / rows)
    Consistency  = 100 * (1 - columns with text issues / total columns)"""
    cells = df.shape[0] * df.shape[1]
    comp = 100 * (1 - df.isna().sum().sum() / cells) if cells else 0.0
    uniq = 100 * (1 - df.duplicated().sum() / len(df)) if len(df) else 0.0
    inc = inconsistency_report(df)
    cons = 100 * (1 - inc["Column"].nunique() / df.shape[1]) if df.shape[1] else 0.0
    return {"completeness": round(comp, 2), "uniqueness": round(uniq, 2),
            "consistency": round(cons, 2), "score": round((comp + uniq + cons) / 3, 2)}


def profile(df: pd.DataFrame) -> dict:
    return {"missing": missing_summary(df), "duplicates": duplicate_summary(df),
            "dtypes": dtype_analysis(df), "inconsistencies": inconsistency_report(df),
            "numeric": numeric_stats(df), "categorical": categorical_stats(df),
            "score": quality_score(df)}
