"""QIMA booking automation, Streamlit edition. Main file path on Streamlit Cloud: streamlit_app/app.py"""
import hmac
import io
import re
import threading
import traceback
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime

import pandas as pd
import streamlit as st

import core
import ui

st.set_page_config(page_title="QIMA booking desk", page_icon=":material/inventory_2:", layout="wide")
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
        st.markdown(ui.hero("QIMA booking desk", "Sign in to start and watch booking runs.", "Private", "ok"), unsafe_allow_html=True)
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
    """Shared by every browser session: a background worker that runs queued runs one after another."""
    rt = {"procs": {}, "lock": threading.Lock(), "cfg": {"env": {}, "timeout": 45, "max_parallel": 1}}

    def loop():
        while True:
            try:
                core.tick(rt, rt["cfg"])
            except Exception:
                traceback.print_exc()
            time.sleep(2)
    threading.Thread(target=loop, daemon=True, name="qima-worker").start()
    return rt


@st.cache_resource(show_spinner="First start: installing the browser, this takes a few minutes...")
def ensure_browser():
    r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                       capture_output=True, text=True, timeout=1200)
    if r.returncode != 0:
        raise RuntimeError((r.stdout + r.stderr)[-1500:])
    return True


MAX_PARALLEL = max(1, int(secret("MAX_PARALLEL", 1)))
runtime()["cfg"].update(env=PORTAL_ENV, timeout=TIMEOUT_MIN, max_parallel=MAX_PARALLEL)


def is_busy(runs):
    return any(m["status"] in ("running", "queued") for m in runs)


def queue_label(runs):
    r, q = sum(m["status"] == "running" for m in runs), sum(m["status"] == "queued" for m in runs)
    return f"{r} running, {q} queued" if q else ("Run in progress" if r else "Ready")


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
    colors = {"DONE": "#e5f5ee;color:#075c3d", "DRYRUN_OK": "#fdf1dc;color:#7a4800",
              "FAILED": "#fbe9e7;color:#8f2118", "PENDING": "#e9eeed;color:#566772"}
    fn = lambda v: f"background-color:{colors[v]};font-weight:600" if v in colors else ""  # noqa: E731
    sty = df.style
    return (sty.map if hasattr(sty, "map") else sty.applymap)(fn, subset=["Status"])


missing = [k for k in ("QIMA_USER", "QIMA_PASS") if k not in PORTAL_ENV]
PAGES = {}
LABEL = {"done": "Done", "failed": "Failed", "running": "Running", "stopped": "Stopped", "created": "Queued", "queued": "Queued"}


def settle():
    """The background worker finalizes runs; the UI only reads their state."""
    return core.list_runs()


def fmt_secs(s):
    s = int(s)
    return f"{s // 3600}h {s % 3600 // 60:02d}m" if s >= 3600 else f"{s // 60}m {s % 60:02d}s"


def run_secs(m):
    if not m.get("started_ts"):
        return 0
    end = datetime.fromisoformat(m["finished"]).timestamp() if m.get("finished") else time.time()
    return max(0, end - m["started_ts"])


def runs_frame(runs):
    rows = []
    for m in runs:
        res = m.get("results", [])
        rows.append({"Run": m["id"], "Started": m["created"].replace("T", " "), "Status": LABEL[m["status"]] + (" (errors)" if m.get("has_errors") and m["status"] == "done" else ""),
                     "Mode": "Dry run" if m.get("dry_run") else "Live", "Bookings": len(res),
                     "Completed": sum(r["status"] in ("DONE", "DRYRUN_OK") for r in res), "Failed": sum(r["status"] == "FAILED" for r in res),
                     "Duration": fmt_secs(run_secs(m)) if m.get("started_ts") else "", "Note": m.get("note", "")})
    return pd.DataFrame(rows)


def page_overview():
    runs = settle()
    busy = is_busy(runs)
    st.markdown(ui.head("Overview", "Health and results across all runs since the app last started.", queue_label(runs), "run" if busy else "ok"), unsafe_allow_html=True)
    res = [r for m in runs for r in m.get("results", [])]
    good, bad = sum(r["status"] in ("DONE", "DRYRUN_OK") for r in res), sum(r["status"] == "FAILED" for r in res)
    ended = [m for m in runs if m.get("finished")]
    avg = fmt_secs(sum(run_secs(m) for m in ended) / len(ended)) if ended else "-"
    st.markdown(ui.kpis([("Runs", len(runs), "info"), ("Bookings processed", len(res), "info"),
                         ("Success rate", f"{round(100 * good / len(res))}%" if res else "-", "ok"),
                         ("Failed bookings", bad, "bad"), ("In queue", sum(m["status"] == "queued" for m in runs), "warn"), ("Average run time", avg, "teal")]), unsafe_allow_html=True)
    left, right = st.columns([2, 1])
    with left:
        st.markdown('<div class="sec">Runs per day</div>', unsafe_allow_html=True)
        if runs:
            df = pd.DataFrame({"day": [m["created"][:10] for m in runs], "status": [LABEL[m["status"]] for m in runs]})
            piv = df.pivot_table(index="day", columns="status", aggfunc="size", fill_value=0).reindex(columns=["Done", "Failed", "Stopped"], fill_value=0)
            st.bar_chart(piv, color=["#0b8a5b", "#c8372d", "#8fa0aa"], height=240)
        else:
            st.markdown(ui.guide(), unsafe_allow_html=True)
    with right:
        st.markdown('<div class="sec">System</div>', unsafe_allow_html=True)
        browser = any((Path.home() / ".cache" / "ms-playwright").glob("chromium*")) if (Path.home() / ".cache" / "ms-playwright").exists() else False
        st.markdown(ui.health([("Dashboard login", "Enabled", True), ("Portal credentials", "Set" if not missing else "Missing " + ", ".join(missing), not missing),
                               ("Browser engine", "Installed" if browser else "Installs on first run", browser), ("Run timeout", f"{TIMEOUT_MIN} min", True),
                               ("Parallel runs", str(MAX_PARALLEL), True), ("Queue", queue_label(runs), True)]), unsafe_allow_html=True)
    if runs:
        st.markdown('<div class="sec">Recent runs</div>', unsafe_allow_html=True)
        st.dataframe(runs_frame(runs[:8]).drop(columns=["Note"]), use_container_width=True, hide_index=True)


def page_new():
    runs = settle()
    busy = is_busy(runs)
    st.markdown(ui.head("New run", "Upload the input files, check the previews, then start or add to the queue.", queue_label(runs), "run" if busy else "ok"), unsafe_allow_html=True)
    st.markdown('<div class="sec">Input files<small>Empty slots reuse the previous run\'s files, so you only upload what changed.</small></div>', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(ui.slot_head(1, "Booking list", "booking_list.xlsx", "#6366f1"), unsafe_allow_html=True)
            f_list = st.file_uploader("booking_list.xlsx", type=["xlsx"], label_visibility="collapsed", help="The list of bookings and their Status.")
        with c2:
            st.markdown(ui.slot_head(2, "Booking file", "booking.xlsx", "#0ea5e9"), unsafe_allow_html=True)
            f_book = st.file_uploader("booking.xlsx", type=["xlsx"], label_visibility="collapsed", help="Uploaded on the General Information step.")
        with c3:
            st.markdown(ui.slot_head(3, "PO PDFs", "one PDF per PO", "#f43f5e"), unsafe_allow_html=True)
            f_pdf = st.file_uploader("PO PDFs", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")
        with c4:
            st.markdown(ui.slot_head(4, "Technical sheet", "TI Excel", "#f59e0b"), unsafe_allow_html=True)
            f_ti = st.file_uploader("Technical sheet (TI) Excel", type=["xlsx"], label_visibility="collapsed", help="Attached in the PO box after the last PO PDF.")

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
        if o2.button("Add to queue" if busy else "Start run", type="primary", use_container_width=True, disabled=bool(missing)):
            issues = core.validate_inputs(f_list.getvalue() if f_list else None, [(f.name, f.getvalue()) for f in f_pdf or []])
            for msg in issues:
                st.error(msg)
            try:
                if issues:
                    st.stop()
                ensure_browser()
                rd = core.create_run(f_book.getvalue() if f_book else None, f_list.getvalue() if f_list else None,
                                     [(f.name, f.getvalue()) for f in f_pdf or []], dry,
                                     ti=f_ti.getvalue() if f_ti else None)
                st.session_state["view"] = rd.name
                st.switch_page(PAGES["monitor"])
            except st.errors.StreamlitAPIException:
                raise
            except Exception as e:
                st.error(str(e))
        if busy:
            st.info("Another run is in progress. This one waits in the queue and starts automatically when it finishes.")



def page_history():
    runs = settle()
    st.markdown(ui.head("History", "Every run kept on this server. Storage resets when the app restarts.", f"{len(runs)} runs", "ok"), unsafe_allow_html=True)
    if not runs:
        st.markdown('<div class="card">No runs yet.</div>', unsafe_allow_html=True)
        return
    df = runs_frame(runs)
    c1, c2 = st.columns([2, 3])
    pick = c1.multiselect("Status", sorted(df["Status"].unique()), default=sorted(df["Status"].unique()))
    q = c2.text_input("Search run or note")
    df = df[df["Status"].isin(pick)]
    if q:
        df = df[df.apply(lambda r: q.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    ev = st.dataframe(df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
    if ev.selection.rows:
        rid = df.iloc[ev.selection.rows[0]]["Run"]
        if st.button(f"Open run {rid}", type="primary"):
            st.session_state["view"] = rid
            st.switch_page(PAGES["monitor"])
    else:
        st.caption("Select a row to open that run.")


# ------------------------------------------------------------ run monitor
def render(rid):
    rd = core.RUNS / rid
    proc = runtime()["procs"].get(rid)
    m = core.load_meta(rd)
    cur, step_shots, _, text = core.log_info(rd)
    shots = sorted(p.name for p in (rd / "logs").glob("*.png"))
    rows = core.read_bookings(rd)
    running = m["status"] == "running"
    queued = m["status"] == "queued"
    qpos = (core.queue_ids().index(rid) + 1) if queued and rid in core.queue_ids() else 0

    st.markdown(f'<div class="sec">Run {rid}<small>{LABEL[m["status"]]}' + (f" · position {qpos} in the queue" if queued else "")
                + (f' · booking {cur["n"]} of {cur["total"]}, ref {cur["ref"]}' if cur and running else "") + "</small></div>", unsafe_allow_html=True)
    if m["note"]:
        st.markdown(f'<div class="note {"bad" if m["status"] == "failed" else "warn"}">{m["note"]}</div>', unsafe_allow_html=True)

    end = datetime.fromisoformat(m["finished"]).timestamp() if m.get("finished") else time.time()
    secs = int(end - m["started_ts"]) if m.get("started_ts") else 0
    cnt = lambda *s: sum(r["Status"] in s for r in rows)  # noqa: E731
    st.markdown(ui.kpis([("Bookings", len(rows), "info"), ("Completed", cnt("DONE", "DRYRUN_OK"), "ok"),
                         ("Failed", cnt("FAILED"), "bad"), ("Pending", cnt("PENDING"), "warn"),
                         ("Elapsed", f"{secs // 60}m {secs % 60:02d}s", "teal")]), unsafe_allow_html=True)
    st.markdown(ui.rail(core.progress(step_shots, m["status"])), unsafe_allow_html=True)

    b1, b2, b3, _ = st.columns([1, 1.2, 1.6, 3])
    if running or queued:
        if b1.button("Cancel" if queued else "Stop run", key="stop_" + rid):
            core.stop(rd, proc)
            st.rerun()
    else:
        if b1.button("Retry", key="retry_" + rid, disabled=bool(missing),
                     help="Adds a run with the same files to the queue; rows already DONE are skipped."):
            try:
                ensure_browser()
                new = core.create_run(None, None, [], m.get("dry_run", False), base=rd)
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
    if render(rid) not in ("running", "queued"):
        st.rerun()



def page_monitor():
    runs = settle()
    busy = is_busy(runs)
    st.markdown(ui.head("Run monitor", "Live progress, bookings, files and screenshots for one run.", queue_label(runs), "run" if busy else "ok"), unsafe_allow_html=True)
    if not runs:
        st.markdown('<div class="card">No runs yet. Start one from <b>New run</b>.</div>', unsafe_allow_html=True)
        return
    ids = [m["id"] for m in runs]
    cur = st.session_state.get("view") if st.session_state.get("view") in ids else ids[0]
    info = {m["id"]: m for m in runs}
    rid = st.selectbox("Run", ids, index=ids.index(cur), key="view_sel", format_func=lambda i: f"{LABEL[info[i]['status']]}  ·  {info[i]['created'][5:16].replace('T', ' ')}  ·  {i[-4:]}")
    st.session_state["view"] = rid
    if core.load_meta(core.RUNS / rid)["status"] in ("running", "queued"):
        live(rid)
    else:
        render(rid)


PAGES["overview"] = st.Page(page_overview, title="Overview", icon=":material/dashboard:", default=True)
PAGES["new"] = st.Page(page_new, title="New run", icon=":material/upload_file:")
PAGES["monitor"] = st.Page(page_monitor, title="Run monitor", icon=":material/monitoring:")
PAGES["history"] = st.Page(page_history, title="History", icon=":material/history:")
nav = st.navigation(list(PAGES.values()))
with st.sidebar:
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()
nav.run()
