# Bebersih - Automated Data Cleaning Website

A Streamlit application for profiling, cleaning and exporting tabular data. Built as a Data Analyst portfolio project.
Every metric, chart and report figure is computed from the uploaded dataset. The original data is never modified:
cleaning always runs on a separate copy, so results are reproducible.

## Main Features
- **Upload:** CSV (automatic encoding and delimiter detection) or Excel (.xlsx, .xls) with sheet selection, file information and dataset preview
- **Data Quality Analysis:** missing values, duplicate records, data type analysis, inconsistent text and date formats, numeric and categorical statistics, and a transparent quality score
- **Outlier Detection:** IQR method (1.5 x IQR) with interactive Plotly boxplots, detected outlier records, and a per-column Keep / Remove / Capping plan with a before/after preview
- **Data Cleaning (user-approved, never automatic):**
  - Missing values: drop rows, mean, median, mode or custom value, chosen per column
  - Duplicates: all columns or selected columns, keep first or last occurrence
  - Text cleaning: trim whitespace, collapse repeated spaces, capitalisation set per column (for example Title Case for city names and UPPERCASE for abbreviations)
  - Data type conversion: integer, float, string, datetime, with warnings for failed conversions
  - Date standardisation: flexible parsing and a user-chosen output format
  - Rename columns and fix values (typos and inconsistent labels) through an editable table
  - Outlier treatment integrated from the Outlier Detection page
- **Safety:** preview before applying, a warning and explicit confirmation when rows may be removed, and settings that are remembered when you switch pages
- **Before & After Comparison:** KPI cards, interactive charts, data previews and a summary of changes
- **Cleaning Report:** issues found, methods chosen, operations performed, remaining issues, data type changes and a quality score before and after
- **Export:** custom file name, then download as CSV, Excel (.xlsx) or a text report
- **Themes:** light and dark mode (configured in `.streamlit/config.toml`)

## Technology Stack
Python, Streamlit, Pandas, NumPy, OpenPyXL, Plotly, Pytest

## Project Structure
```
app.py                          Streamlit UI (pages only)
requirements.txt
.streamlit/config.toml          Light and dark theme settings
modules/data_loader.py          File reading, encoding and delimiter handling
modules/data_profiler.py        Data quality analysis and quality score
modules/outlier_detector.py     IQR detection and treatment
modules/data_cleaner.py         Cleaning operations and the ordered pipeline
modules/data_validator.py       Validation of datasets and cleaning configuration
modules/report_generator.py     Before/after metrics and report text
utils/helpers.py                Shared helpers
utils/export.py                 CSV / Excel / text export and file name sanitising
tests/                          Pytest unit tests
sample_messy_data.csv           Example dataset to try the app
```

## Installation
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Streamlit 1.50 or newer is required.

## Run
```bash
streamlit run app.py
python -m pytest                 # run the unit tests
```

## Example Usage
1. **Dashboard:** upload `sample_messy_data.csv` (or your own file).
2. **Data Quality Analysis:** review missing values, duplicates, whitespace, capitalisation variants and mixed date formats.
3. **Outlier Detection:** inspect the boxplot and records, then choose Keep, Remove or Capping per column.
4. **Data Cleaning:** work through the tabs (Missing Values, Duplicates, Text, Data Types, Dates, Outliers, Rename & Replace), review the preview, confirm if rows may be removed, then click Apply cleaning.
5. **Before & After Comparison / Cleaning Report:** check the effect of your choices. If something was missed, go back to Data Cleaning, adjust the settings and apply again.
6. **Export Dataset:** type a file name and download the CSV, Excel or report.

## Design Decisions
- **The original dataset is always the source.** Each time you apply cleaning, the whole configuration runs again on the original data. Nothing is applied twice, and mistakes are fixed by changing a setting and applying again.
- **Fixed pipeline order:** replace values, text cleaning, dates, data types, duplicates, missing values, outliers, rename columns.
  - Value fixes run first because the table shows values exactly as they appear in the original data.
  - Duplicates are removed before imputation so that imputation cannot create false duplicates.
  - Renaming runs last so every other setting can keep referring to the original column names.
- **Integer conversion is refused** if it would drop decimals. Failed conversions are reported as new missing values.
- **Outlier counts after cleaning are recomputed** on the cleaned data with the same IQR method. After capping, quartiles shift, so a few borderline points can still be flagged.
- **Outliers are not assumed to be errors.** Detection never changes data. Extreme values can be valid business cases, so the choice is left to the user.
- **Quality score is transparent:** the average of Completeness (share of non-missing cells), Uniqueness (share of non-duplicate rows) and Consistency (share of columns without whitespace, capitalisation or date-format issues), each from 0 to 100.
- **Empty cells in the Fix values table are ignored**, so values are never deleted by accident.

## Known Limitations
- IQR assumes a roughly symmetric distribution. Skewed columns (for example prices or durations) often show many outliers that are valid, and binary 0/1 columns are not meaningful for IQR analysis.
- Fix values uses exact matching and is limited to text columns with at most 200 unique values.
- Reading old `.xls` files requires the `xlrd` package (included in `requirements.txt`).

## Screenshots
Add screenshots here (for example `docs/dashboard.png`, `docs/outliers.png`, `docs/comparison.png`).