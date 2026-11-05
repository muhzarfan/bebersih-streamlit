"""Input validation for DataFrames and cleaning configuration."""
import pandas as pd


def validate_dataframe(df) -> list:
    """Return a list of blocking problems (empty list = valid)."""
    if df is None or not isinstance(df, pd.DataFrame):
        return ["No dataset loaded."]
    problems = []
    if df.shape[1] == 0:
        problems.append("The dataset has no columns.")
    if df.shape[0] == 0:
        problems.append("The dataset has no rows.")
    return problems


def empty_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns if df[c].isna().all()]


def config_is_destructive(config: dict) -> bool:
    """"True if the configuration may remove rows or columns."""
    if config.get("drop_columns"):
        return True
    if config.get("duplicates", {}).get("enabled"):
        return True
    if any(r.get("method") == "drop_rows" for r in config.get("missing", {}).values()):
        return True
    return any(v == "remove" for v in config.get("outliers", {}).values())


def validate_config(config: dict, df: pd.DataFrame) -> list:
    """Return warnings about config entries that reference unknown columns."""
    cols = set(df.columns)
    issues = []
    for section in ("missing", "types", "outliers", "rename", "replace", "drop_columns", "type_options"):
        for c in config.get(section, {}):
            if c not in cols:
                issues.append(f"Column '{c}' in '{section}' does not exist.")
    return issues
