"""QIMA booking automation, Streamlit edition. Main file path on Streamlit Cloud: streamlit_app/app.py"""
import hmac
import io
import re
import subprocess
import sys
import time
from datetime import datetime

import pandas as pd
import streamlit as st

import core
import ui

st.set_page_config(page_title="QIMA Booking Automation", page_icon="Q", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)


def secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return default


# ------------------------------------------------------------------ login
APP_PASSWORD = secret("APP_PASSWORD")
if not APP_PASSWORD:
    st.error("Add APP_PASSWORD to this app's Secrets (see STREAMLIT.md), then reload.")
    st.stop()
if not st.session_state.get("ok"):
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(ui.hero("QIMA Booking Automation", "Sign in to control your booking runs", "Secure access", "ok"), unsafe_allow_html=True)
        with st.form("login"):
            pw = st.text_input("Dashboard password", type="password")
            if st.form_submit_button("Sign in", type="primary", use_container_width=True):
                if hmac.compare_digest(pw, str(APP_PASSWORD)):
                    st.session_state["ok"] = True
                    st.rerun()
                st.error("Wrong password")
    st.stop()

# -------------------------------------------------------- shared resources
TIMEOUT_MIN = int(secret("RUN_TIMEOUT_MIN", 45))
PORTAL_ENV = {k: str(v) for k, v in dict(st.secrets).items() if isinstance(v, (str, int, float)) and k != "APP_PASSWORD"}


@st.cache_resource
def runtime():
    return {"proc": None, "dir": None}  # one run at a time, shared by every browser session


@st.cache_resource(show_spinner="First start: installing the browser, this takes a few minutes...")
def ensure_browser():
    r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                       capture_output=True, text=True, timeout=1200)
    if r.returncode != 0:
        raise RuntimeError((r.stdout + r.stderr)[-1500:])
    return True


def active_run():
    rt = runtime()
    return rt["dir"] if rt["dir"] and rt["proc"] is not None and rt["proc"].poll() is None else None


def launch(rd, dry_run):
    rt = runtime()
    rt["proc"] = core.start(rd, PORTAL_ENV, dry_run)
    rt["dir"] = rd


# ----------------------------------------------------------- Excel preview
@st.cache_data(show_spinner=False)
def excel_sheets(data: bytes) -> dict:
    """Every sheet as a tidy table: empty rows/columns dropped, header = the fullest of the first rows."""
    out = {}
    for name, df in pd.read_excel(io.BytesIO(data), sheet_name=None, header=None, dtype=str, engine="openpyxl").items():
        df = df.dropna(how="all").dropna(axis=1, how="all")
        if df.empty:
            continue
        hdr = df.head(6).notna().sum(axis=1).idxmax()
        pos = df.index.get_loc(hdr)
        seen, cols = {}, []
        for i, c in enumerate(df.iloc[pos]):
            c = str(c).strip()[:48] if pd.notna(c) else f"col {i + 1}"
            seen[c] = seen.get(c, 0) + 1
            cols.append(c if seen[c] == 1 else f"{c} ({seen[c]})")
        body = df.iloc[pos + 1:].copy()
        body.columns = cols
        out[name] = body.fillna("").head(300)
    return out


def show_excel(data: bytes):
    try:
        sheets = excel_sheets(data)
    except Exception as e:
        st.warning(f"Could not read this Excel file: {e}")
        return
    if not sheets:
        st.caption("This workbook is empty.")
        return
    names = list(sheets)
    holders = st.tabs(names) if len(names) > 1 else [st.container()]
    for holder, n in zip(holders, names):
        with holder:
            df = sheets[n]
            st.caption(f"{len(df)} rows, {len(df.columns)} columns")
            st.dataframe(df, use_container_width=True, hide_index=True, height=min(420, 40 + 35 * len(df)))


def po_numbers(data: bytes) -> list:
    try:
        for df in excel_sheets(data).values():
            for c in df.columns:
                if re.search(r"p\.?\s*o\.?\s*no", str(c), re.I):
                    vals = [re.sub(r"\D", "", str(v)) for v in df[c]]
                    vals = [v for v in vals if v]
                    if vals:
                        return vals
    except Exception:
        pass
    return []


def status_style(df):
    colors = {"DONE": "#d1fae5;color:#065f46", "DRYRUN_OK": "#fef3c7;color:#92400e",
              "FAILED": "#fee2e2;color:#991b1b", "PENDING": "#e2e8f0;color:#475569"}
    fn = lambda v: f"background-color:{colors[v]};font-weight:600" if v in colors else ""  # noqa: E731
    sty = df.style
    return (sty.map if hasattr(sty, "map") else sty.applymap)(fn, subset=["Status"])


# ------------------------------------------------------------------ header
for _m in core.list_runs():  # settle finished runs first so the list and header are current
    if _m["status"] == "running":
        _rd = core.RUNS / _m["id"]
        core.refresh_status(_rd, runtime()["proc"] if runtime()["dir"] == _rd else None, TIMEOUT_MIN)
runs = core.list_runs()
busy = active_run() is not None
st.markdown(ui.hero("QIMA Booking Automation", "Upload your files, start the run and watch every step live.",
                    "Run in progress" if busy else "Ready", "run" if busy else "ok"), unsafe_allow_html=True)
missing = [k for k in ("QIMA_USER", "QIMA_PASS") if k not in PORTAL_ENV]
if missing:
    st.markdown(f'<div class="note warn">Add {" and ".join(missing)} to this app\'s Secrets before starting a run.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------ new run card
st.markdown('<div class="sec">New run<small>Empty slots reuse the previous run\'s files, so you only upload what changed.</small></div>', unsafe_allow_html=True)
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    f_list = c1.file_uploader("1  booking_list.xlsx", type=["xlsx"], help="The list of bookings and their Status.")
    f_book = c2.file_uploader("2  booking.xlsx", type=["xlsx"], help="Uploaded on the General Information step.")
    f_pdf = c3.file_uploader("3  PO PDFs", type=["pdf"], accept_multiple_files=True)
    f_ti = c4.file_uploader("4  Technical sheet (TI) Excel", type=["xlsx"], help="Attached in the PO box after the last PO PDF.")

    previews = [(n, f) for n, f in (("booking_list.xlsx", f_list), ("booking.xlsx", f_book), ("Technical sheet (TI)", f_ti)) if f]
    if previews:
        st.markdown("**Uploaded Excel files**")
        for tab, (label, f) in zip(st.tabs([f"{n}  ({f.size // 1024 or 1} KB)" for n, f in previews]), previews):
            with tab:
                show_excel(f.getvalue())
    if f_ti and f_pdf:
        pos, names = po_numbers(f_ti.getvalue()), " ".join(re.sub(r"\D", "", p.name) for p in f_pdf)
        if pos:
            pairs = [(p, p in names or p.lstrip("0") in names) for p in dict.fromkeys(pos)]
            have = sum(ok for _, ok in pairs)
            st.markdown(f"**PO coverage**: {have} of {len(pairs)} POs in the TI sheet have a PDF")
            st.markdown(ui.po_chips(pairs), unsafe_allow_html=True)
    elif f_pdf:
        st.caption(f"{len(f_pdf)} PO PDF(s) selected: " + ", ".join(p.name for p in f_pdf[:8]) + (" ..." if len(f_pdf) > 8 else ""))

    o1, o2 = st.columns([3, 1])
    dry = o1.checkbox("Dry run: stop at Inspection Details and mark rows DRYRUN_OK", value=False)
    if o2.button("Start run", type="primary", use_container_width=True, disabled=busy or bool(missing)):
        try:
            ensure_browser()
            rd = core.create_run(f_book.getvalue() if f_book else None, f_list.getvalue() if f_list else None,
                                 [(f.name, f.getvalue()) for f in f_pdf or []], dry,
                                 ti=f_ti.getvalue() if f_ti else None)
            launch(rd, dry)
            st.session_state["view"] = rd.name
            st.rerun()
        except Exception as e:
            st.error(str(e))
    if busy:
        st.info("A run is in progress. Wait for it to finish or stop it below.")

# ---------------------------------------------------------------- sidebar
LABEL = {"done": "Done", "failed": "Failed", "running": "Running", "stopped": "Stopped", "created": "Queued"}
DOT = {"done": "🟢", "failed": "🔴", "running": "🟠", "stopped": "⚪", "created": "⚪"}
with st.sidebar:
    st.markdown('<div class="brand"><div class="logo">Q</div><b>QIMA Automation</b></div>', unsafe_allow_html=True)
    st.caption("Run history")
    if runs:
        ids = [m["id"] for m in runs]
        if st.session_state.get("view") not in ids:
            st.session_state["view"] = ids[0]
        info = {m["id"]: m for m in runs}
        st.radio("Run", ids, key="view", label_visibility="collapsed", format_func=lambda i: (
            f"{DOT[info[i]['status']]} {LABEL[info[i]['status']]}"
            f"{' with errors' if info[i]['has_errors'] and info[i]['status'] == 'done' else ''}  ·  {info[i]['created'][5:16].replace('T', ' ')}"))
    else:
        st.write("No runs yet.")
    st.divider()
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

if not runs:
    st.stop()


# ------------------------------------------------------------ run monitor
def render(rid):
    rd = core.RUNS / rid
    rt = runtime()
    proc = rt["proc"] if rt["dir"] == rd else None
    m = core.refresh_status(rd, proc, TIMEOUT_MIN)
    cur, step_shots, _, text = core.log_info(rd)
    shots = sorted(p.name for p in (rd / "logs").glob("*.png"))
    rows = core.read_bookings(rd)
    running = m["status"] == "running"

    st.markdown(f'<div class="sec">Run {rid}<small>{LABEL[m["status"]]}'
                + (f' · booking {cur["n"]} of {cur["total"]}, ref {cur["ref"]}' if cur and running else "") + "</small></div>", unsafe_allow_html=True)
    if m["note"]:
        st.markdown(f'<div class="note {"bad" if m["status"] == "failed" else "warn"}">{m["note"]}</div>', unsafe_allow_html=True)

    end = datetime.fromisoformat(m["finished"]).timestamp() if m.get("finished") else time.time()
    secs = int(end - m["started_ts"]) if m.get("started_ts") else 0
    cnt = lambda *s: sum(r["Status"] in s for r in rows)  # noqa: E731
    st.markdown(ui.kpis([("Bookings", len(rows), "info"), ("Completed", cnt("DONE", "DRYRUN_OK"), "ok"),
                         ("Failed", cnt("FAILED"), "bad"), ("Pending", cnt("PENDING"), "warn"),
                         ("Elapsed", f"{secs // 60}m {secs % 60:02d}s", "info")]), unsafe_allow_html=True)
    st.markdown(ui.rail(core.progress(step_shots, m["status"])), unsafe_allow_html=True)

    b1, b2, b3, _ = st.columns([1, 1.2, 1.6, 3])
    if running:
        if b1.button("Stop run", key="stop_" + rid):
            core.stop(rd, proc)
            st.rerun()
    else:
        if b1.button("Retry", key="retry_" + rid, disabled=active_run() is not None or bool(missing),
                     help="Runs again with the same files; rows already DONE are skipped."):
            try:
                ensure_browser()
                new = core.create_run(None, None, [], m.get("dry_run", False), base=rd)
                launch(new, m.get("dry_run", False))
                st.session_state["view"] = new.name
                st.rerun()
            except Exception as e:
                st.error(str(e))
        b2.download_button("Download all", core.make_zip(rd), file_name=f"run-{rid}.zip", key="zip_" + rid)
        lst = rd / "input" / "booking_list.xlsx"
        if lst.exists():
            b3.download_button("Updated booking_list.xlsx", lst.read_bytes(), file_name="booking_list.xlsx", key="lst_" + rid)

    t_book, t_xl, t_log, t_shot = st.tabs(["Bookings", "Excel files used", "Live log", f"Screenshots ({len(shots)})"])
    with t_book:
        if rows:
            st.dataframe(status_style(pd.DataFrame(rows)), use_container_width=True, hide_index=True)
        else:
            st.caption("Rows from booking_list.xlsx appear here.")
    with t_xl:
        files = {"booking_list.xlsx": rd / "input" / "booking_list.xlsx", "booking.xlsx": rd / "input" / "booking.xlsx",
                 "Technical sheet (TI)": rd / "input" / "technical_info.xlsx"}
        files = {k: v for k, v in files.items() if v.exists()}
        if files:
            pick = st.radio("File", list(files), horizontal=True, key="xl_" + rid, label_visibility="collapsed")
            show_excel(files[pick].read_bytes())
        else:
            st.caption("No Excel files in this run.")
        pdfs = sorted((rd / "input" / "po_pdf").glob("*.pdf"))
        if pdfs:
            st.caption(f"{len(pdfs)} PO PDFs: " + ", ".join(p.name for p in pdfs[:10]) + (" ..." if len(pdfs) > 10 else ""))
    with t_log:
        st.code(text[-6000:] or "Waiting for output...", language=None)
    with t_shot:
        show = shots[-1:] if running else shots
        if running and shots:
            st.caption("Showing the latest screenshot while the run is in progress.")
        for i in range(0, len(show), 4):
            for col, name in zip(st.columns(4), show[i:i + 4]):
                col.image(str(rd / "logs" / name), use_container_width=True,
                          caption=("ERROR: " if core.FAIL_SHOT_RE.search(name) else "") + name[:-4])
        if not shots:
            st.caption("Screenshots from the script appear here.")
    return m["status"]


@st.fragment(run_every=2)
def live(rid):
    if render(rid) != "running":
        st.rerun()


rid = st.session_state["view"]
status = core.refresh_status(core.RUNS / rid, runtime()["proc"] if runtime()["dir"] == core.RUNS / rid else None, TIMEOUT_MIN)["status"]
if status == "running":
    live(rid)
else:
    render(rid)
