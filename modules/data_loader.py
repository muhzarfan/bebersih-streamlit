"""Load CSV / Excel files with encoding and delimiter handling."""
import csv
import io
import os

import pandas as pd

ENCODINGS = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]


class LoadError(Exception):
    """Raised with a user-friendly message when a file cannot be read."""


def is_excel(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in (".xlsx", ".xls", ".xlsm")


def get_excel_sheets(data: bytes) -> list:
    try:
        return pd.ExcelFile(io.BytesIO(data)).sheet_names
    except ImportError as e:
        raise LoadError(f"A required library is missing for this Excel format: {e}")
    except Exception as e:
        raise LoadError(f"The Excel file could not be read: {e}")


def _decode(data: bytes):
    for enc in ENCODINGS:
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise LoadError("Unable to detect the file encoding.")


def load_csv(data: bytes):
    if not data or not data.strip():
        raise LoadError("The file is empty.")
    text, enc = _decode(data)
    try:
        delim = csv.Sniffer().sniff(text[:20000], delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    try:
        df = pd.read_csv(io.StringIO(text), sep=delim)
    except Exception as e:
        raise LoadError(f"The CSV file could not be parsed: {e}")
    return df, {"encoding": enc, "delimiter": repr(delim)}


def load_file(data: bytes, filename: str, sheet=None):
    """Return (DataFrame, info dict). Raises LoadError on failure."""
    if is_excel(filename):
        try:
            df = pd.read_excel(io.BytesIO(data), sheet_name=sheet or 0)
        except Exception as e:
            raise LoadError(f"The Excel file could not be read: {e}")
        info = {"type": "Excel", "sheet": sheet or "first sheet"}
    elif filename.lower().endswith((".csv", ".txt", ".tsv")):
        df, info = load_csv(data)
        info["type"] = "CSV"
    else:
        raise LoadError("Unsupported file type. Please upload a CSV or Excel file.")
    if df.empty or df.shape[1] == 0:
        raise LoadError("The dataset contains no rows or no columns.")
    info["size_kb"] = round(len(data) / 1024, 1)
    info["name"] = filename
    return df, info
