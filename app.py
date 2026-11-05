"""Bebersih - Automated Data Cleaning Platform (Streamlit entry point).
UI only: all data logic lives in modules/ and utils/."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules import data_cleaner as dc
from modules import data_loader as dl
from modules import data_profiler as dp
from modules import data_validator as dv
from modules import outlier_detector as od
from modules import report_generator as rg
from utils import export
from utils.helpers import is_numeric, is_text_dtype

st.set_page_config(page_title="Bebersih", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container{padding-top:2rem;max-width:1300px}
[data-testid="stMetric"]{background:rgba(128,128,128,0.08);border:1px solid rgba(128,128,128,0.25);
border-radius:8px;padding:12px 16px}
h1,h2,h3{font-weight:600;letter-spacing:-0.01em}
</style>""", unsafe_allow_html=True)

PAGES = ["Dashboard", "Data Quality Analysis", "Outlier Detection", "Data Cleaning",
         "Before & After Comparison", "Cleaning Report", "Export Dataset"]
ACCENT = ["#2F6FEB", "#9AA5B1"]


def init_state():
    for k, v in {"original": None, "file_info": {}, "file_sig": None, "profile": None,
                 "outlier_summary": None, "config": dc.default_config(), "cleaned": None,
                 "log": [], "report": None}.items():
        st.session_state.setdefault(k, v)


@st.cache_data(show_spinner=False)
def cached_profile(df):
    return dp.profile(df)

@st.cache_data(show_spinner="Preparing files...")
def cached_exports(df):
    return export.to_csv_bytes(df), export.to_excel_bytes(df)

@st.cache_data(show_spinner=False)
def cached_outliers(df):
    return od.summarize(df)

WIDGET_PREFIXES = ("mv_", "mvv_", "dup_", "tx_", "ty_", "dt_", "rn_", "rnsel", "rpsel", "ex_", "dcsel", "dcthr")
MAX_UNIQUE_REPLACE = 200

def reset_results():
    st.session_state.update(cleaned=None, log=[], report=None, config=dc.default_config(),
                            saved_widgets={}, replace_saved={}, replace_snapshot={})

def restore_widgets():
    for k, v in st.session_state.get("saved_widgets", {}).items():
        st.session_state.setdefault(k, v)

def save_widgets():
    st.session_state.saved_widgets = {k: v for k, v in st.session_state.items()
                                      if isinstance(k, str) and k.startswith(WIDGET_PREFIXES)}

def require_data():
    if st.session_state.original is None:
        st.info("No dataset loaded. Upload a file on the Dashboard page first.")
        st.stop()
    return st.session_state.original


def require_cleaned():
    require_data()
    if st.session_state.cleaned is None:
        st.info("No cleaning has been applied yet. Configure and apply it on the Data Cleaning page.")
        st.stop()
    return st.session_state.cleaned


# ------------------------------------------------------------------ pages
def page_dashboard():
    st.title("Dashboard")
    st.caption("Upload a CSV or Excel file to begin. The original dataset is kept unchanged throughout.")
    up = st.file_uploader("Dataset file", type=["csv", "txt", "tsv", "xlsx", "xls", "xlsm"])
    if up is not None:
        data = up.getvalue()
        sheet = None
        try:
            if dl.is_excel(up.name):
                sheets = dl.get_excel_sheets(data)
                sheet = st.selectbox("Excel sheet", sheets) if len(sheets) > 1 else sheets[0]
            sig = (up.name, len(data), sheet)
            if st.session_state.file_sig != sig:
                df, info = dl.load_file(data, up.name, sheet)
                problems = dv.validate_dataframe(df)
                if problems:
                    raise dl.LoadError(" ".join(problems))
                st.session_state.update(original=df, file_info=info, file_sig=sig)
                st.session_state.profile = cached_profile(df)
                st.session_state.outlier_summary = cached_outliers(df)
                reset_results()
        except dl.LoadError as e:
            st.error(f"Could not load the file. {e}")
            return
    df = st.session_state.original
    if df is None:
        st.info("Waiting for a file upload.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Total rows", f"{len(df):,}")
    c2.metric("Total columns", f"{df.shape[1]:,}")
    c3.metric("Cells", f"{df.size:,}")
    with st.expander("File information", expanded=True):
        st.table(pd.DataFrame({"Property": list(st.session_state.file_info),
                               "Value": [str(v) for v in st.session_state.file_info.values()]}))
    empty = dv.empty_columns(df)
    if empty:
        st.warning(f"Empty columns detected: {', '.join(map(str, empty))}")
    st.subheader("Dataset preview")
    st.dataframe(df.head(200), width="stretch")


def page_quality():
    st.title("Data Quality Analysis")
    df = require_data()
    p = st.session_state.profile or cached_profile(df)
    sc = p["score"]
    cols = st.columns(4)
    cols[0].metric("Quality score", f"{sc['score']}")
    cols[1].metric("Completeness", f"{sc['completeness']}")
    cols[2].metric("Uniqueness", f"{sc['uniqueness']}")
    cols[3].metric("Consistency", f"{sc['consistency']}")
    st.caption("Quality score = average of Completeness (share of non-missing cells), Uniqueness "
               "(share of non-duplicate rows) and Consistency (share of columns without whitespace, "
               "capitalisation or date-format issues). All components are 0-100.")
    t1, t2, t3, t4, t5 = st.tabs(["Missing Values", "Duplicates", "Data Types", "Inconsistencies", "Statistics"])
    with t1:
        m = p["missing"]
        st.metric("Total missing values", f"{int(m['Missing Count'].sum()):,}")
        st.dataframe(m, width="stretch", hide_index=True)
        if m["Missing Count"].sum() > 0:
            fig = px.bar(m[m["Missing Count"] > 0], x="Column", y="Missing %", color_discrete_sequence=ACCENT[:1])
            st.plotly_chart(fig, width="stretch")
        else:
            st.success("No missing values detected.")
    with t2:
        d = p["duplicates"]
        a, b = st.columns(2)
        a.metric("Duplicate rows", f"{d['count']:,}")
        b.metric("Duplicate %", f"{d['percent']}%")
        if d["count"] and st.checkbox("Show duplicated records"):
            st.dataframe(d["rows"], width="stretch")
    with t3:
        st.dataframe(p["dtypes"], width="stretch", hide_index=True)
    with t4:
        if p["inconsistencies"].empty:
            st.success("No inconsistent values detected.")
        else:
            st.dataframe(p["inconsistencies"], width="stretch", hide_index=True)
    with t5:
        st.subheader("Numeric columns")
        st.dataframe(p["numeric"], width="stretch", hide_index=True)
        st.subheader("Categorical columns")
        st.dataframe(p["categorical"], width="stretch", hide_index=True)
        cat = [c for c in df.columns if not is_numeric(df[c]) and df[c].notna().any()]
        if cat:
            c = st.selectbox("Value frequency for column", cat)
            vc = df[c].astype(str).value_counts().head(15).reset_index()
            vc.columns = [c, "Count"]
            st.plotly_chart(px.bar(vc, x=c, y="Count", color_discrete_sequence=ACCENT[:1]), width="stretch")


def page_outliers():
    st.title("Outlier Detection")
    df = require_data()
    st.caption("Method: IQR. Lower = Q1 - 1.5 x IQR, Upper = Q3 + 1.5 x IQR. Missing values are ignored. "
               "Detection never modifies data, and extreme values may be valid business cases.")
    summ = st.session_state.outlier_summary
    if summ is None:
        summ = cached_outliers(df)
    if summ.empty:
        st.info("The dataset has no numeric columns.")
        return
    st.dataframe(summ, width="stretch", hide_index=True)
    ok = summ[summ["Status"] == "OK"]["Column"].tolist()
    if not ok:
        st.warning("No numeric column has enough valid values for IQR analysis.")
        return
    col = st.selectbox("Column to inspect", ok)
    b = od.iqr_bounds(df[col])
    fig = go.Figure(go.Box(x=df[col].astype(float), name=col, boxpoints="outliers",
                           marker_color=ACCENT[0], boxmean=False))
    fig.add_vline(x=b["lower"], line_dash="dash", line_color="#D64545", annotation_text="Lower bound")
    fig.add_vline(x=b["upper"], line_dash="dash", line_color="#D64545", annotation_text="Upper bound")
    st.plotly_chart(fig, width="stretch")
    st.subheader("Detected outlier records")
    rec = od.outlier_records(df, ok)
    st.dataframe(rec, width="stretch", hide_index=True)

    st.subheader("Outlier treatment plan")
    st.caption("Choose an action per column. Nothing is applied until you confirm on the Data Cleaning page.")
    plan = {}
    flagged = summ[summ["Outlier Count"] > 0]["Column"].tolist()
    labels = {"Keep Outliers": "keep", "Remove Outliers": "remove", "Capping / Winsorization": "cap"}
    inv = {v: k for k, v in labels.items()}
    for c in flagged:
        cur = inv.get(st.session_state.config["outliers"].get(c, "keep"), "Keep Outliers")
        choice = st.selectbox(c, list(labels), index=list(labels).index(cur), key=f"ol_{c}")
        plan[c] = labels[choice]
    st.session_state.config["outliers"] = {c: a for c, a in plan.items() if a != "keep"}
    if flagged:
        treated, log = od.treat(df, plan)
        st.subheader("Preview (not applied)")
        a, b2 = st.columns(2)
        a.metric("Rows before", f"{len(df):,}")
        b2.metric("Rows after treatment", f"{len(treated):,}", delta=len(treated) - len(df))
        pv = od.summarize(treated, flagged)[["Column", "Outlier Count"]].merge(
            summ[["Column", "Outlier Count"]], on="Column", suffixes=(" After", " Before"))
        st.dataframe(pv[["Column", "Outlier Count Before", "Outlier Count After"]], hide_index=True)
        st.caption("After capping, quartiles are recomputed on the treated data, so a few new borderline "
                   "points can still be flagged.")


def page_cleaning():
    st.title("Data Cleaning")
    df = require_data()
    restore_widgets()
    st.caption("Cleaning is always applied to the original dataset using the settings below, so results are "
               "reproducible. Your settings are remembered when you leave this page.")
    if st.session_state.cleaned is not None:
        st.info("A cleaned dataset already exists. Applying cleaning again replaces it with the new result.")
    cfg = dc.default_config()
    cfg["outliers"] = dict(st.session_state.config.get("outliers", {}))
    cols = list(df.columns)
    t = st.tabs(["Missing Values", "Duplicates", "Text", "Data Types", "Dates", "Outliers", "Rename & Replace", "Drop Columns"])
    with t[0]:
        miss_cols = [c for c in cols if df[c].isna().any()]
        if not miss_cols:
            st.success("No missing values in this dataset.")
        for c in miss_cols:
            opts = dc.METHODS if is_numeric(df[c]) else [m for m in dc.METHODS if m not in ("Mean", "Median")]
            a, b = st.columns([2, 1])
            m = a.selectbox(f"{c} ({int(df[c].isna().sum())} missing, {df[c].dtype})", opts, key=f"mv_{c}")
            val = b.text_input("Value", key=f"mvv_{c}") if m == "Custom value" else ""
            if m != "No action":
                cfg["missing"][c] = {"method": dc.method_key(m), "value": val}
    with t[1]:
        if st.checkbox("Remove duplicate rows", key="dup_on"):
            sub = st.multiselect("Columns used to detect duplicates (empty = all columns)", cols, key="dup_sub")
            keep = st.radio("Keep", ["First", "Last"], horizontal=True, key="dup_keep")
            cfg["duplicates"] = {"enabled": True, "subset": sub, "keep": keep}
    with t[2]:
        tcols = st.multiselect("Columns to clean", [c for c in cols if is_text_dtype(df[c])], key="tx_cols")
        if tcols:
            case_opts = {"No change": "none", "lowercase": "lower", "UPPERCASE": "upper", "Title Case": "title"}
            st.caption("Capitalisation is set per column, e.g. Title Case for city names and UPPERCASE for abbreviations.")
            cases = {c: case_opts[st.selectbox(f"Capitalisation for: {c}", list(case_opts), key=f"tx_k_{c}")]
                     for c in tcols}
            cfg["text"] = {"columns": tcols,
                           "strip": st.checkbox("Trim leading/trailing whitespace", True, key="tx_s"),
                           "collapse": st.checkbox("Collapse repeated spaces", True, key="tx_c"),
                           "case": cases}
    with t[3]:
        pick = st.multiselect("Columns to convert", cols, key="ty_cols")
        for c in pick:
            to = st.selectbox(f"{c} (currently {df[c].dtype})", ["Integer", "Float", "String", "Datetime"], key=f"ty_{c}")
            cfg["types"][c] = to
    with t[4]:
        dcols = st.multiselect("Date columns", cols, key="dt_cols")
        if dcols:
            fmt = st.selectbox("Output format", ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d %b %Y"], key="dt_f")
            first = st.checkbox("Treat ambiguous dates as day-first (e.g. 05/02/2024 = 5 Feb)", key="dt_d")
            cfg["dates"] = {"columns": dcols, "format": fmt, "dayfirst": first}
    with t[5]:
        if cfg["outliers"]:
            st.write("Plan chosen on the Outlier Detection page:")
            st.table(pd.DataFrame({"Column": list(cfg["outliers"]), "Action": list(cfg["outliers"].values())}))
        else:
            st.info("All outliers are kept. Set a plan on the Outlier Detection page to change this.")
    with t[6]:
        st.subheader("Rename columns")
        st.caption("Leave a field empty to keep the original name. Renaming is applied last, after all other steps.")
        rn_sel = st.multiselect("Columns to rename", cols, key="rnsel")
        for c in rn_sel:
            new = st.text_input(f"New name for: {c}", placeholder=str(c), key=f"rn_{c}").strip()
            if new and new != c:
                cfg["rename"][c] = new
        st.subheader("Fix values (typos, inconsistent labels)")
        st.caption("Edit the New Value cell to replace a value. Matching is exact, uses the values exactly as they "
                   "appear in the original data, and runs before text cleaning. Empty cells are ignored.")
        rp_sel = st.multiselect("Text columns to fix", [c for c in cols if is_text_dtype(df[c])], key="rpsel")
        snapshot = st.session_state.get("replace_snapshot", {})
        saved_rules = {}
        for c in rp_sel:
            vals = df[c].dropna()
            vc = vals[vals.map(lambda v: isinstance(v, str))].value_counts().sort_index().sort_values(
                ascending=False, kind="stable")
            if len(vc) > MAX_UNIQUE_REPLACE:
                st.info(f"{c} has {len(vc)} unique values, which is too many to edit in a table.")
                continue
            prev = snapshot.get(c, {})
            base = pd.DataFrame({"Current Value": vc.index, "Count": vc.values,
                                 "New Value": [prev.get(v, v) for v in vc.index]})
            edited = st.data_editor(base, key=f"rpedit_{c}", hide_index=True, width="stretch",
                                    disabled=["Current Value", "Count"])
            rules = {o: n for o, n in zip(edited["Current Value"], edited["New Value"])
                     if isinstance(n, str) and n != o}
            saved_rules[c] = rules
            if rules:
                cfg["replace"][c] = rules
        st.session_state.replace_saved = saved_rules
    with t[7]:
        st.caption("Dropped columns are removed first, so settings for them in other tabs are ignored, and "
                   "duplicates are detected on the remaining columns.")
        miss_pct = df.isna().mean().mul(100).round(2)
        st.session_state.setdefault("dcthr", 50.0)
        thr = st.number_input("Suggest columns with missing values above (%)", min_value=0.0, max_value=100.0,
                              step=5.0, key="dcthr")
        sugg = [c for c in cols if miss_pct[c] > thr]
        st.button(f"Select {len(sugg)} suggested column(s)", disabled=not sugg,
                  on_click=lambda s=sugg: st.session_state.update(dcsel=s))
        cfg["drop_columns"] = st.multiselect("Columns to drop", cols, key="dcsel")
        st.dataframe(pd.DataFrame({"Column": cols, "Type": [str(df[c].dtype) for c in cols],
                                   "Missing %": [miss_pct[c] for c in cols]}).sort_values(
            "Missing %", ascending=False), hide_index=True, width="stretch")
    save_widgets()
    st.divider()
    st.subheader("Preview")
    for w in dv.validate_config(cfg, df):
        st.warning(w)
    preview, log = dc.run_pipeline(df, cfg)
    a, b, c, d = st.columns(4)
    a.metric("Rows", f"{len(preview):,}", delta=len(preview) - len(df))
    b.metric("Missing values", f"{int(preview.isna().sum().sum()):,}",
             delta=int(preview.isna().sum().sum() - df.isna().sum().sum()))
    c.metric("Duplicate rows", f"{int(preview.duplicated().sum()):,}",
             delta=int(preview.duplicated().sum() - df.duplicated().sum()))
    d.metric("Columns", f"{preview.shape[1]:,}", delta=preview.shape[1] - df.shape[1])
    for e in log:
        if e["level"] == "warning":
            st.warning(f"{e['operation']} / {e['column']}: {e['detail']}")
    if log:
        st.dataframe(pd.DataFrame(log)[["operation", "column", "affected", "detail"]], hide_index=True,
                     width="stretch")
    st.dataframe(preview.head(100), width="stretch")
    destructive = dv.config_is_destructive(cfg)
    lost = len(df) - len(preview)
    confirmed = True
    if destructive:
        st.warning(f"These settings may remove data: {lost} row(s) and {df.shape[1] - preview.shape[1]} "
                   "column(s) in this preview.")
        confirmed = st.checkbox("I understand and confirm that data may be removed", key="confirm_loss")
    if st.button("Apply cleaning", type="primary", disabled=not confirmed):
        st.session_state.cleaned, st.session_state.log = preview, log
        st.session_state.config = cfg
        st.session_state.report = rg.build_report(df, preview, cfg, log, st.session_state.file_info)
        st.success("Cleaning applied. The original dataset is unchanged. See Comparison, Report and Export.")


def page_compare():
    st.title("Before & After Comparison")
    df, cl = require_data(), require_cleaned()
    rep = st.session_state.report
    b, a = rep["before"], rep["after"]
    labels = {"rows": "Total Rows", "columns": "Total Columns", "missing": "Missing Values",
              "duplicates": "Duplicate Rows", "outlier_records": "Outlier Records"}
    cols = st.columns(5)
    for col, k in zip(cols, labels):
        col.metric(labels[k], f"{a[k]:,}", delta=a[k] - b[k], delta_color="inverse" if k != "columns" else "off")
    tbl = pd.DataFrame({"Metric": list(labels.values()), "Original Dataset": [b[k] for k in labels],
                        "Cleaned Dataset": [a[k] for k in labels]})
    st.dataframe(tbl, hide_index=True, width="stretch")
    q = tbl[tbl["Metric"].isin(["Missing Values", "Duplicate Rows", "Outlier Records"])].melt(
        "Metric", var_name="Dataset", value_name="Count")
    st.plotly_chart(px.bar(q, x="Metric", y="Count", color="Dataset", barmode="group",
                           color_discrete_sequence=ACCENT[::-1]), width="stretch")
    st.caption("Outlier records for the cleaned dataset are recomputed with the same IQR method (k = 1.5).")
    c1, c2 = st.columns(2)
    c1.subheader("Before cleaning")
    c1.dataframe(df.head(100), width="stretch")
    c2.subheader("After cleaning")
    c2.dataframe(cl.head(100), width="stretch")
    st.subheader("Summary of changes")
    if st.session_state.log:
        st.dataframe(pd.DataFrame(st.session_state.log)[["operation", "column", "affected", "detail"]],
                     hide_index=True, width="stretch")
    else:
        st.info("No operations were selected; the cleaned dataset equals the original.")


def page_report():
    st.title("Cleaning Report")
    require_data(); require_cleaned()
    rep = st.session_state.report
    b, a = rep["before"], rep["after"]
    c1, c2 = st.columns(2)
    c1.metric("Quality score before", b["score"])
    c2.metric("Quality score after", a["score"], delta=round(a["score"] - b["score"], 2))
    st.caption("Score = mean of Completeness, Uniqueness and Consistency (see Data Quality Analysis).")
    with st.expander("Detected issues in the original dataset", expanded=True):
        st.write("Missing values by column"); st.dataframe(rep["issues"]["missing"], hide_index=True)
        st.write("Text inconsistencies"); st.dataframe(rep["issues"]["inconsistencies"], hide_index=True)
        st.write("Outlier summary"); st.dataframe(rep["issues"]["outliers"], hide_index=True)
    with st.expander("Remaining issues after cleaning"):
        st.write(f"Remaining missing values: {a['missing']}  |  Remaining duplicate rows: {a['duplicates']}")
        st.dataframe(rep["remaining_outliers"], hide_index=True)
    with st.expander("Data type changes"):
        st.dataframe(pd.DataFrame(rep["type_changes"], columns=["Column", "Before", "After"]), hide_index=True)
    st.text_area("Full report", rg.to_text(rep), height=420)


def page_export():
    st.title("Export Dataset")
    require_data(); cl = require_cleaned()
    restore_widgets()
    st.write(f"Exporting the cleaned dataset: {len(cl):,} rows, {cl.shape[1]} columns.")
    st.session_state.setdefault("ex_name", "cleaned_dataset")
    name = st.text_input("File name (without extension)", key="ex_name",
                         help="Illegal characters are removed and spaces become underscores. Empty = default name.")
    save_widgets()
    base = export.safe_filename(name)
    st.caption(f"Files: {base}.csv, {base}.xlsx, {base}_report.txt")
    csv_bytes, xlsx_bytes = cached_exports(cl)
    c1, c2, c3, _ = st.columns([1, 1, 1, 2], gap="small")
    c1.download_button("Download CSV", csv_bytes, f"{base}.csv", "text/csv", width="stretch")
    c2.download_button("Download Excel", xlsx_bytes, f"{base}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    c3.download_button("Download Report", export.to_text_bytes(rg.to_text(st.session_state.report)),
                       f"{base}_report.txt", "text/plain", width="stretch")


def main():
    init_state()
    with st.sidebar:
        st.markdown("### Bebersih")
        st.caption("Automated Data Cleaning Website")
        page = st.radio("Navigation", PAGES, label_visibility="collapsed")
        st.divider()
        if st.session_state.get("last_page") != page:  # entering a page: freeze saved value fixes as table defaults
            st.session_state.replace_snapshot = {c: dict(m) for c, m in st.session_state.get("replace_saved", {}).items()}
            st.session_state.last_page = page
        if st.session_state.original is not None:
            st.caption(f"Dataset: {st.session_state.file_info.get('name', '')}")
            st.progress(1.0 if st.session_state.cleaned is not None else 0.4,
                        text="Cleaned" if st.session_state.cleaned is not None else "Loaded, not cleaned")
    {"Dashboard": page_dashboard, "Data Quality Analysis": page_quality, "Outlier Detection": page_outliers,
     "Data Cleaning": page_cleaning, "Before & After Comparison": page_compare,
     "Cleaning Report": page_report, "Export Dataset": page_export}[page]()


main()
