"""Styling and small HTML helpers for the Streamlit front end."""
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input { font-family: 'Inter', system-ui, sans-serif !important; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }
.block-container { padding-top: 1.4rem; max-width: 1280px; }
[data-testid="stSidebar"] { background: #0c1c28; }
[data-testid="stSidebar"] * { color: #dbe7ee; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #fff; }
[data-testid="stSidebar"] button { background: #14303f; border: 1px solid #28495b; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding: 6px 8px; border-radius: 8px; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #14303f; }
.brand { display:flex; align-items:center; gap:10px; margin-bottom:6px; }
.brand .logo { width:34px; height:34px; border-radius:9px; background:linear-gradient(135deg,#14b8a6,#0f766e); display:grid; place-items:center; color:#fff; font-weight:700; }
.brand b { font-size:1.05rem; color:#fff; letter-spacing:.02em; }
.hero { background:linear-gradient(120deg,#0c1c28 0%,#0f4c5c 55%,#0f766e 100%); color:#fff; padding:26px 30px; border-radius:16px; display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap; box-shadow:0 10px 30px rgba(12,28,40,.18); margin-bottom:18px; }
.hero h1 { margin:0; font-size:1.7rem; font-weight:700; letter-spacing:-.01em; color:#fff; padding:0; }
.hero p { margin:4px 0 0; color:#b9d3dc; }
.chip { display:inline-flex; align-items:center; gap:8px; padding:7px 14px; border-radius:99px; background:rgba(255,255,255,.14); font-weight:600; font-size:.9rem; }
.chip .dot { width:9px; height:9px; border-radius:50%; background:#94a3b8; }
.chip.run .dot { background:#fbbf24; animation:pulse 1.3s infinite; } .chip.ok .dot { background:#34d399; } .chip.bad .dot { background:#f87171; }
@keyframes pulse { 50% { opacity:.3; } }
@media (prefers-reduced-motion: reduce) { .chip.run .dot, .st.active i { animation:none !important; } }
.card { background:#fff; border:1px solid #e1e8ee; border-radius:14px; padding:18px 20px; margin:0 0 14px; box-shadow:0 1px 2px rgba(16,32,43,.04); }
.sec { font-size:1.05rem; font-weight:700; margin:6px 0 10px; color:#10202b; }
.sec small { font-weight:500; color:#64748b; margin-left:8px; }
.kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:8px 0 16px; }
.kpi { background:#fff; border:1px solid #e1e8ee; border-radius:14px; padding:14px 16px; border-left:5px solid #94a3b8; }
.kpi small { color:#64748b; font-weight:500; } .kpi b { display:block; font-size:1.7rem; line-height:1.2; color:#10202b; }
.kpi.ok { border-left-color:#10b981; } .kpi.bad { border-left-color:#ef4444; } .kpi.warn { border-left-color:#f59e0b; } .kpi.info { border-left-color:#0f766e; }
.rail { display:flex; margin:10px 0 18px; }
.st { flex:1; text-align:center; position:relative; font-size:.85rem; color:#64748b; font-weight:500; }
.st i { display:inline-grid; place-items:center; width:32px; height:32px; border-radius:50%; background:#e2e8f0; color:#64748b; font-style:normal; font-weight:700; position:relative; z-index:1; }
.st::before { content:""; position:absolute; top:14px; left:-50%; width:100%; height:4px; background:#e2e8f0; }
.st:first-child::before { display:none; }
.st span { display:block; margin-top:6px; }
.st.done i { background:#0f766e; color:#fff; } .st.done::before { background:#0f766e; } .st.done { color:#10202b; }
.st.active i { background:#f59e0b; color:#fff; animation:pulse 1.3s infinite; } .st.active::before { background:linear-gradient(90deg,#0f766e,#f59e0b); } .st.active { color:#10202b; font-weight:700; }
.st.failed i { background:#ef4444; color:#fff; } .st.failed::before { background:#0f766e; } .st.failed { color:#b91c1c; font-weight:700; }
.st.stopped i { background:#64748b; color:#fff; }
.po { display:inline-block; padding:3px 11px; margin:3px 4px 3px 0; border-radius:99px; font-size:.82rem; font-weight:600; }
.po.ok { background:#d1fae5; color:#065f46; } .po.no { background:#fee2e2; color:#991b1b; }
.note { padding:10px 14px; border-radius:10px; margin:6px 0 12px; font-weight:500; }
.note.bad { background:#fee2e2; color:#991b1b; } .note.warn { background:#fef3c7; color:#92400e; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#14b8a6,#0f766e); border:0; font-weight:600; border-radius:10px; }
.stButton > button, .stDownloadButton > button { border-radius:10px; }
[data-testid="stFileUploader"] section { border-radius:12px; border:1.5px dashed #9fb3c0; background:#f8fafc; }
.stTabs [data-baseweb="tab"] { font-weight:600; }
</style>
"""


def hero(title, subtitle, chip_text, chip_kind):
    return (f'<div class="hero"><div><h1>{title}</h1><p>{subtitle}</p></div>'
            f'<div class="chip {chip_kind}"><span class="dot"></span>{chip_text}</div></div>')


def kpis(items):
    return '<div class="kpis">' + "".join(
        f'<div class="kpi {k}"><small>{label}</small><b>{value}</b></div>' for label, value, k in items) + "</div>"


def rail(steps):
    parts = []
    for i, (label, s) in enumerate(steps, 1):
        mark = {"done": "&#10003;", "failed": "&#10005;", "stopped": "&#9632;"}.get(s, str(i))
        parts.append(f'<div class="st {s}"><i>{mark}</i><span>{label}</span></div>')
    return '<div class="rail">' + "".join(parts) + "</div>"


def po_chips(pairs):
    return "".join(f'<span class="po {"ok" if ok else "no"}">{po}</span>' for po, ok in pairs)
