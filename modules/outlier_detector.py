"""IQR outlier detection and treatment. Functions never mutate their input."""
import numpy as np
import pandas as pd

from utils.helpers import is_numeric, pct

MIN_VALID = 4  # minimum numeric observations required to compute IQR
K = 1.5


def numeric_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns if is_numeric(df[c])]


def iqr_bounds(s: pd.Series, k: float = K):
    """Return IQR statistics ignoring NaN, or None if too few valid values."""
    v = pd.to_numeric(s, errors="coerce").dropna().astype(float)
    if len(v) < MIN_VALID:
        return None
    q1, q3 = float(v.quantile(0.25)), float(v.quantile(0.75))
    iqr = q3 - q1
    return {"q1": q1, "q3": q3, "iqr": iqr, "lower": q1 - k * iqr,
            "upper": q3 + k * iqr, "n_valid": int(len(v))}


def outlier_mask(s: pd.Series, bounds) -> pd.Series:
    if bounds is None:
        return pd.Series(False, index=s.index)
    v = pd.to_numeric(s, errors="coerce").astype(float)
    return ((v < bounds["lower"]) | (v > bounds["upper"])).fillna(False)


def summarize(df: pd.DataFrame, cols=None, k: float = K) -> pd.DataFrame:
    rows = []
    for c in (cols if cols is not None else numeric_columns(df)):
        b = iqr_bounds(df[c], k)
        if b is None:
            rows.append({"Column": c, "Q1": np.nan, "Q3": np.nan, "IQR": np.nan,
                         "Lower Bound": np.nan, "Upper Bound": np.nan,
                         "Outlier Count": 0, "Outlier %": 0.0,
                         "Status": f"Insufficient data (< {MIN_VALID} valid values)"})
            continue
        n = int(outlier_mask(df[c], b).sum())
        rows.append({"Column": c, "Q1": b["q1"], "Q3": b["q3"], "IQR": b["iqr"],
                     "Lower Bound": b["lower"], "Upper Bound": b["upper"],
                     "Outlier Count": n, "Outlier %": pct(n, b["n_valid"]), "Status": "OK"})
    return pd.DataFrame(rows, columns=["Column", "Q1", "Q3", "IQR", "Lower Bound",
                                       "Upper Bound", "Outlier Count", "Outlier %", "Status"])


def outlier_records(df: pd.DataFrame, cols=None, k: float = K) -> pd.DataFrame:
    parts = []
    for c in (cols if cols is not None else numeric_columns(df)):
        b = iqr_bounds(df[c], k)
        m = outlier_mask(df[c], b)
        if b is not None and m.any():
            parts.append(pd.DataFrame({"Row Index": df.index[m], "Column": c,
                                       "Outlier Value": df.loc[m, c].values,
                                       "Lower Bound": b["lower"], "Upper Bound": b["upper"]}))
    if not parts:
        return pd.DataFrame(columns=["Row Index", "Column", "Outlier Value", "Lower Bound", "Upper Bound"])
    return pd.concat(parts, ignore_index=True)


def count_outlier_records(df: pd.DataFrame, cols=None, k: float = K) -> int:
    """Number of distinct rows with an outlier in at least one column."""
    flag = pd.Series(False, index=df.index)
    for c in (cols if cols is not None else numeric_columns(df)):
        flag |= outlier_mask(df[c], iqr_bounds(df[c], k))
    return int(flag.sum())


def treat(df: pd.DataFrame, plan: dict, k: float = K):
    """Apply {column: 'keep'|'remove'|'cap'}. Returns (new_df, log list)."""
    out, log = df.copy(), []
    for c, action in plan.items():
        if action == "keep" or c not in out.columns:
            continue
        b = iqr_bounds(out[c], k)
        if b is None:
            log.append({"operation": "Outlier Treatment", "column": c, "affected": 0, "level": "warning",
                        "detail": "Skipped: too few valid numeric values."})
            continue
        m = outlier_mask(out[c], b)
        n = int(m.sum())
        if action == "remove":
            out = out.loc[~m]
            detail = f"Removed {n} row(s) outside [{b['lower']:.4g}, {b['upper']:.4g}]"
        elif action == "cap":
            lo, hi = b["lower"], b["upper"]
            if pd.api.types.is_integer_dtype(out[c]):
                lo, hi = np.ceil(lo), np.floor(hi)
            out[c] = out[c].clip(lower=lo, upper=hi)
            detail = f"Capped {n} value(s) to [{b['lower']:.4g}, {b['upper']:.4g}]"
        else:
            continue
        log.append({"operation": f"Outlier Treatment ({action})", "column": c,
                    "affected": n, "detail": detail, "level": "info"})
    return out, log
