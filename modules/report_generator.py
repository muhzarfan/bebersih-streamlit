"""Build the cleaning report from real before/after data."""
import pandas as pd

from modules import data_profiler as dp
from modules import outlier_detector as od
from modules import data_cleaner as dc

def metrics(df: pd.DataFrame) -> dict:
    return {"rows": int(df.shape[0]), "columns": int(df.shape[1]),
            "missing": int(df.isna().sum().sum()),
            "duplicates": int(df.duplicated().sum()),
            "outlier_records": od.count_outlier_records(df),
            "score": dp.quality_score(df)["score"]}


def build_report(original, cleaned, config, log, file_info=None) -> dict:
    before, after = metrics(original), metrics(cleaned)
    ren = (config or {}).get("rename") or {}
    new_name = lambda c: ren.get(c, c) if ren.get(c, c) in cleaned.columns else c
    changes = []
    for c in original.columns:
        n = new_name(c)
        if n in cleaned.columns:
            b_dt, a_dt = str(original[c].dtype), str(cleaned[n].dtype)
            b_lb, a_lb = dc.current_type_label(original[c]), dc.current_type_label(cleaned[n])
            if b_dt != a_dt or b_lb != a_lb:
                changes.append({"Column": n, "Before": f"{b_dt} ({b_lb})", "After": f"{a_dt} ({a_lb})"})
    return {"file_info": file_info or {}, "before": before, "after": after,
            "issues": {"inconsistencies": dp.inconsistency_report(original),
                       "missing": dp.missing_summary(original),
                       "outliers": od.summarize(original)},
            "config": config, "log": log, "type_changes": changes,
            "remaining_outliers": od.summarize(cleaned)}


def to_text(rep: dict) -> str:
    b, a = rep["before"], rep["after"]
    L = ["DATA CLEANING REPORT", "=" * 60, "", "1. ORIGINAL DATASET"]
    L += [f"  {k}: {v}" for k, v in rep["file_info"].items()]
    L += [f"  Rows: {b['rows']}  Columns: {b['columns']}", "", "2. DETECTED ISSUES",
          f"  Missing values: {b['missing']}", f"  Duplicate rows: {b['duplicates']}",
          f"  Rows with outliers (IQR 1.5): {b['outlier_records']}",
          f"  Text inconsistencies found: {len(rep['issues']['inconsistencies'])}", "",
          "3. SELECTED CLEANING METHODS"]
    c = rep["config"]
    L += [f"  Text: {c.get('text') or '-'}", f"  Dates: {c.get('dates') or '-'}",
          f"  Types: {c.get('types') or '-'}", f"  Duplicates: {c.get('duplicates') or '-'}",
          f"  Missing: {c.get('missing') or '-'}", f"  Outliers: {c.get('outliers') or '-'}",
          f"  Rename columns: {c.get('rename') or '-'}", f"  Replace values: {c.get('replace') or '-'}",
          f"  Drop columns: {c.get('drop_columns') or '-'}", "",
          "4. OPERATIONS PERFORMED"]
    L += [f"  [{e['level'].upper()}] {e['operation']} | {e['column']} | affected={e['affected']} | {e['detail']}"
          for e in rep["log"]] or ["  None"]
    L += ["", "5. RESULT", f"  Rows: {b['rows']} -> {a['rows']}", f"  Columns: {b['columns']} -> {a['columns']}",
          f"  Remaining missing values: {a['missing']}", f"  Remaining duplicate rows: {a['duplicates']}",
          f"  Remaining rows with outliers: {a['outlier_records']} (recomputed with the same IQR method)",
          "", "6. DATA TYPE CHANGES"]
    L += [f"  {t['Column']}: {t['Before']} -> {t['After']}" for t in rep["type_changes"]] or ["  None"]
    L += ["", "7. DATA QUALITY SCORE",
          "  Score = mean(Completeness, Uniqueness, Consistency); each is 0-100.",
          f"  Before: {b['score']}   After: {a['score']}"]
    return "\n".join(L)


def to_csv_table(rep: dict) -> pd.DataFrame:
    return pd.DataFrame([{"Metric": k, "Original": rep["before"][k], "Cleaned": rep["after"][k]}
                         for k in rep["before"]])
