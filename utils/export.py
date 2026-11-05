"""Export helpers: convert DataFrames / reports to downloadable bytes."""
import io
import re
import pandas as pd


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Cleaned Data") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buf.getvalue()


def to_text_bytes(text: str) -> bytes:
    return text.encode("utf-8")

_ILLEGAL = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def safe_filename(name, default: str = "cleaned_dataset") -> str:
    """Make a user-typed name safe for a file: no illegal characters, no extension, spaces -> underscores."""
    name = _ILLEGAL.sub("", (name or "").strip())
    name = re.sub(r"\.(csv|xlsx|xls|txt)$", "", name, flags=re.I).strip(" .")
    name = re.sub(r"\s+", "_", name)
    return name[:100] or default