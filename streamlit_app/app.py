"""QIMA RPA control, Streamlit edition. Main file path on Streamlit Cloud: streamlit_app/app.py"""
import hmac
import subprocess
import sys

import streamlit as st

import core

st.set_page_config(page_title="QIMA RPA control", layout="wide")


def secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return default


# ------------------------------------------------------------------ login
APP_PASSWORD = secret("APP_PASSWORD")
if not APP_PASSWORD:
    st.error("Add APP_PASSWORD to this app's Secrets (see the setup notes), then reload.")
    st.stop()
if not st.session_state.get("ok"):
    st.title("QIMA RPA control")
    with st.form("login"):
        pw = st.text_input("Dashboard password", type="password")
        if st.form_submit_button("Sign in"):
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
    if rt["dir"] and rt["proc"] is not None and rt["proc"].poll() is None:
        return rt["dir"]
    return None


def launch(rd, dry_run):
    rt = runtime()
    rt["proc"] = core.start(rd, PORTAL_ENV, dry_run)
    rt["dir"] = rd


# ------------------------------------------------------------ start form
st.title("QIMA RPA control")
missing = [k for k in ("QIMA_USER", "QIMA_PASS") if k not in PORTAL_ENV]
if missing:
    st.warning("Add " + " and ".join(missing) + " to this app's Secrets before starting a run.")

runs = core.list_runs()
with st.expander("Start a new run", expanded=not runs):
    c1, c2, c3 = st.columns(3)
    f_book = c1.file_uploader("booking.xlsx", type=["xlsx"])
    f_list = c2.file_uploader("booking_list.xlsx", type=["xlsx"])
    f_pdf = c3.file_uploader("PO PDFs", type=["pdf"], accept_multiple_files=True)
    st.caption("Empty slots reuse the previous run's files, including its Status column, so rows already DONE "
               "are skipped. This app's storage is wiped when it restarts or sleeps: after that, upload "
               "the updated booking_list.xlsx you downloaded from the last run.")
    dry = st.checkbox("Dry run (stop at Inspection Details, rows marked DRYRUN_OK)", value=False)
    if st.button("Start run", type="primary", disabled=active_run() is not None or bool(missing)):
        try:
            ensure_browser()
            rd = core.create_run(f_book.getvalue() if f_book else None, f_list.getvalue() if f_list else None,
                                 [(f.name, f.getvalue()) for f in f_pdf or []], dry)
            launch(rd, dry)
            st.session_state["view"] = rd.name
            st.rerun()
        except Exception as e:
            st.error(str(e))
    if active_run() is not None:
        st.info("A run is in progress. Wait for it to finish or stop it below.")

# ---------------------------------------------------------------- history
runs = core.list_runs()
if not runs:
    st.stop()
ids = [m["id"] for m in runs]
LABEL = {"done": "Done", "failed": "Failed", "running": "Running", "stopped": "Stopped", "created": "Queued"}
if st.session_state.get("view") not in ids:
    st.session_state["view"] = ids[0]
with st.sidebar:
    st.header("Run history")
    st.selectbox("Run", ids, key="view", format_func=lambda i: next(
        f"{LABEL[m['status']]}{' with errors' if m['has_errors'] and m['status'] == 'done' else ''}  {m['created'][5:16].replace('T', ' ')}"
        for m in runs if m["id"] == i))
    if st.button("Sign out"):
        st.session_state.clear()
        st.rerun()

COLOR = {"done": "green", "active": "orange", "failed": "red", "stopped": "gray", "pending": "gray"}


def render(rid):
    rd = core.RUNS / rid
    rt = runtime()
    proc = rt["proc"] if rt["dir"] == rd else None
    m = core.refresh_status(rd, proc, TIMEOUT_MIN)
    cur, step_shots, _, text = core.log_info(rd)
    shots = sorted(p.name for p in (rd / "logs").glob("*.png"))

    st.subheader(f"Run {rid}")
    badge = {"done": "green", "failed": "red", "running": "orange", "stopped": "gray"}.get(m["status"], "gray")
    st.markdown(f":{badge}[**{LABEL[m['status']]}**]" + (f"  Booking {cur['n']} of {cur['total']}, ref {cur['ref']}" if cur and m["status"] == "running" else ""))
    if m["note"]:
        st.markdown(f":{'red' if m['status'] == 'failed' else 'orange'}[{m['note']}]")

    steps = core.progress(step_shots, m["status"])
    st.progress(sum(s == "done" for _, s in steps) / len(steps))
    for col, (label, s) in zip(st.columns(len(steps)), steps):
        col.markdown(f":{COLOR[s]}[{label}]")

    b1, b2, b3 = st.columns([1, 1, 4])
    if m["status"] == "running":
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

    rows = core.read_bookings(rd)
    st.markdown("**Bookings**")
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.caption("Rows from booking_list.xlsx appear here.")
    lst = rd / "input" / "booking_list.xlsx"
    if lst.exists() and m["status"] != "running":
        st.download_button("Download updated booking_list.xlsx", lst.read_bytes(), file_name="booking_list.xlsx", key="lst_" + rid)

    st.markdown("**Live log**")
    st.code(text[-6000:] or "Waiting for output...", language=None)

    if shots:
        running = m["status"] == "running"
        st.markdown(f"**Screenshots** ({len(shots)})")
        show = shots[-1:] if running else shots
        for row in range(0, len(show), 4):
            for col, name in zip(st.columns(4), show[row:row + 4]):
                label = name[:-4]
                col.image(str(rd / "logs" / name), caption=("ERROR: " if core.FAIL_SHOT_RE.search(name) else "") + label, use_container_width=True)
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
