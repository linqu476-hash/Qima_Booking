"""Styling and small HTML helpers for the Streamlit front end."""
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input { font-family: 'Inter', system-ui, sans-serif !important; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }
.stApp { background: linear-gradient(180deg, #e9f0f7 0%, #f7f9fc 45%, #f3f6fb 100%); }
.block-container { padding-top: 3.6rem; max-width: 1280px; }
/* sidebar */
[data-testid="stSidebar"] { background: linear-gradient(185deg, #081521 0%, #0d2f42 60%, #0f4c5c 100%); }
[data-testid="stSidebar"] * { color: #dbe7ee; }
[data-testid="stSidebarNav"]::before { content: "QIMA  Automation"; display: block; margin: 8px 12px 14px; padding: 14px 14px 14px 58px; border-radius: 12px; font-weight: 800; letter-spacing: .04em; color: #fff;
  background: rgba(255,255,255,.07) url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='34' height='34'><rect width='34' height='34' rx='9' fill='%2314b8a6'/><text x='17' y='24' font-size='19' font-weight='800' text-anchor='middle' fill='white' font-family='Arial'>Q</text></svg>") no-repeat 12px center; }
[data-testid="stSidebarNav"] a { border-radius: 10px; margin: 2px 8px; padding: 6px 10px; transition: background .15s; }
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,.09); }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: linear-gradient(90deg, #14b8a6, #0f766e); box-shadow: 0 4px 14px rgba(20,184,166,.35); }
[data-testid="stSidebarNav"] a[aria-current="page"] * { color: #fff; font-weight: 700; }
[data-testid="stSidebar"] button { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.18); }
/* hero */
.hero { background: radial-gradient(circle at 88% 15%, rgba(45,212,191,.40), transparent 38%), radial-gradient(circle at 70% 120%, rgba(99,102,241,.45), transparent 45%), linear-gradient(120deg, #081521 0%, #0f4c5c 55%, #0f766e 100%);
  color: #fff; padding: 26px 30px; border-radius: 18px; display: flex; justify-content: space-between; align-items: center; gap: 18px; flex-wrap: wrap; box-shadow: 0 14px 34px rgba(8,21,33,.22); margin-bottom: 20px; }
.hero h1 { margin: 0; font-size: 1.7rem; font-weight: 800; letter-spacing: -.01em; color: #fff; padding: 0; }
.hero p { margin: 4px 0 0; color: #bfe0e8; }
.hero.compact { padding: 18px 26px; margin-bottom: 18px; } .hero.compact h1 { font-size: 1.4rem; } .hero.compact p { font-size: .92rem; }
.chip { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 99px; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.25); font-weight: 600; font-size: .9rem; backdrop-filter: blur(4px); }
.chip .dot { width: 9px; height: 9px; border-radius: 50%; background: #94a3b8; }
.chip.run .dot { background: #fbbf24; animation: pulse 1.3s infinite; } .chip.ok .dot { background: #34d399; } .chip.bad .dot { background: #f87171; }
@keyframes pulse { 50% { opacity: .3; } }
@media (prefers-reduced-motion: reduce) { .chip.run .dot, .st.active i { animation: none !important; } }
/* cards and sections */
.card { background: #fff; border: 1px solid #e1e8ee; border-radius: 16px; padding: 18px 20px; margin: 0 0 14px; box-shadow: 0 2px 8px rgba(16,32,43,.05); }
.sec { font-size: 1.05rem; font-weight: 800; margin: 8px 0 12px; color: #0f2230; padding-left: 12px; border-left: 4px solid #14b8a6; }
.sec small { font-weight: 500; color: #64748b; margin-left: 8px; }
[data-testid="stVerticalBlockBorderWrapper"] { background: #fff; border-radius: 16px; box-shadow: 0 2px 10px rgba(16,32,43,.06); }
.slot { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.slot .n { width: 30px; height: 30px; border-radius: 9px; display: grid; place-items: center; color: #fff; font-weight: 800; flex: none; }
.slot b { display: block; line-height: 1.2; color: #0f2230; } .slot small { color: #64748b; }
/* KPI cards */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin: 8px 0 18px; }
.kpi { background: #fff; border: 1px solid #e1e8ee; border-radius: 16px; padding: 16px 18px; display: flex; align-items: center; gap: 14px; box-shadow: 0 2px 8px rgba(16,32,43,.05); transition: transform .15s, box-shadow .15s; }
.kpi:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(16,32,43,.10); }
.kpi .ico { width: 46px; height: 46px; border-radius: 13px; display: grid; place-items: center; flex: none; }
.kpi .ico svg { width: 24px; height: 24px; stroke: #fff; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.kpi small { color: #64748b; font-weight: 500; display: block; } .kpi b { font-size: 1.65rem; line-height: 1.15; color: #0f2230; font-weight: 800; }
.kpi.info .ico { background: linear-gradient(135deg, #818cf8, #4f46e5); } .kpi.ok .ico { background: linear-gradient(135deg, #34d399, #059669); }
.kpi.bad .ico { background: linear-gradient(135deg, #fb7185, #e11d48); } .kpi.warn .ico { background: linear-gradient(135deg, #fbbf24, #d97706); }
.kpi.teal .ico { background: linear-gradient(135deg, #2dd4bf, #0f766e); }
/* stepper */
.rail { display: flex; margin: 10px 0 20px; background: #fff; border: 1px solid #e1e8ee; border-radius: 16px; padding: 18px 10px 14px; box-shadow: 0 2px 8px rgba(16,32,43,.05); }
.st { flex: 1; text-align: center; position: relative; font-size: .85rem; color: #64748b; font-weight: 500; }
.st i { display: inline-grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; background: #e2e8f0; color: #64748b; font-style: normal; font-weight: 800; position: relative; z-index: 1; }
.st::before { content: ""; position: absolute; top: 15px; left: -50%; width: 100%; height: 4px; background: #e2e8f0; }
.st:first-child::before { display: none; } .st span { display: block; margin-top: 6px; }
.st.done i { background: linear-gradient(135deg, #2dd4bf, #0f766e); color: #fff; } .st.done::before { background: #0f766e; } .st.done { color: #0f2230; }
.st.active i { background: linear-gradient(135deg, #fbbf24, #d97706); color: #fff; animation: pulse 1.3s infinite; } .st.active::before { background: linear-gradient(90deg, #0f766e, #f59e0b); } .st.active { color: #0f2230; font-weight: 700; }
.st.failed i { background: linear-gradient(135deg, #fb7185, #e11d48); color: #fff; } .st.failed::before { background: #0f766e; } .st.failed { color: #b91c1c; font-weight: 700; }
.st.stopped i { background: #64748b; color: #fff; }
/* misc */
.po { display: inline-block; padding: 3px 11px; margin: 3px 4px 3px 0; border-radius: 99px; font-size: .82rem; font-weight: 600; }
.po.ok { background: #d1fae5; color: #065f46; } .po.no { background: #fee2e2; color: #991b1b; }
.note { padding: 11px 15px; border-radius: 12px; margin: 6px 0 12px; font-weight: 500; }
.note.bad { background: #fee2e2; color: #991b1b; border-left: 4px solid #e11d48; } .note.warn { background: #fef3c7; color: #92400e; border-left: 4px solid #f59e0b; }
.hrow { display: flex; justify-content: space-between; align-items: center; padding: 9px 0; border-bottom: 1px solid #eef2f6; font-size: .9rem; } .hrow:last-child { border: 0; }
.hrow b { padding: 2px 10px; border-radius: 99px; font-size: .78rem; } .hrow b.ok { background: #d1fae5; color: #065f46; } .hrow b.no { background: #fee2e2; color: #991b1b; }
.guide { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 6px 0 18px; }
.guide div { border-radius: 16px; padding: 18px 20px; color: #fff; box-shadow: 0 8px 20px rgba(16,32,43,.12); } .guide b { display: block; font-size: 1.05rem; margin: 6px 0 2px; } .guide span { opacity: .9; font-size: .9rem; }
.guide em { font-style: normal; font-weight: 800; font-size: 1.6rem; opacity: .85; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #14b8a6, #0f766e); border: 0; font-weight: 700; border-radius: 12px; box-shadow: 0 6px 16px rgba(15,118,110,.35); transition: transform .15s; }
.stButton > button[kind="primary"]:hover { transform: translateY(-1px); }
.stButton > button, .stDownloadButton > button { border-radius: 12px; }
[data-testid="stFileUploader"] section { border-radius: 12px; border: 1.5px dashed #9fb3c0; background: #f8fbfd; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { font-weight: 600; background: #fff; border-radius: 10px; padding: 8px 16px; border: 1px solid #e1e8ee; }
.stTabs [aria-selected="true"] { background: #0f766e; color: #fff; border-color: #0f766e; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
</style>
"""


def hero(title, subtitle, chip_text, chip_kind):
    return (f'<div class="hero"><div><h1>{title}</h1><p>{subtitle}</p></div>'
            f'<div class="chip {chip_kind}"><span class="dot"></span>{chip_text}</div></div>')


ICONS = {
    "info": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "ok": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4 12 14.01l-3-3"/>',
    "bad": '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>',
    "warn": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "teal": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
}


def kpis(items):
    return '<div class="kpis">' + "".join(
        f'<div class="kpi {k}"><div class="ico"><svg viewBox="0 0 24 24">{ICONS[k]}</svg></div><div><small>{label}</small><b>{value}</b></div></div>'
        for label, value, k in items) + "</div>"


def slot_head(n, title, hint, color):
    return f'<div class="slot"><div class="n" style="background:{color}">{n}</div><div><b>{title}</b><small>{hint}</small></div></div>'


def guide():
    cards = [("1", "Upload files", "Add your Excel files and PO PDFs, and preview them instantly.", "linear-gradient(135deg,#6366f1,#4338ca)"),
             ("2", "Start the run", "Choose a dry run first, then start the automation.", "linear-gradient(135deg,#14b8a6,#0f766e)"),
             ("3", "Review results", "Follow each step live and check screenshots and statuses.", "linear-gradient(135deg,#f59e0b,#d97706)")]
    return '<div class="guide">' + "".join(f'<div style="background:{bg}"><em>{n}</em><b>{t}</b><span>{d}</span></div>' for n, t, d, bg in cards) + "</div>"


def rail(steps):
    parts = []
    for i, (label, s) in enumerate(steps, 1):
        mark = {"done": "&#10003;", "failed": "&#10005;", "stopped": "&#9632;"}.get(s, str(i))
        parts.append(f'<div class="st {s}"><i>{mark}</i><span>{label}</span></div>')
    return '<div class="rail">' + "".join(parts) + "</div>"


def po_chips(pairs):
    return "".join(f'<span class="po {"ok" if ok else "no"}">{po}</span>' for po, ok in pairs)


def head(title, subtitle, chip_text, chip_kind):
    return hero(title, subtitle, chip_text, chip_kind).replace('class="hero"', 'class="hero compact"', 1)


def health(rows):
    return '<div class="card">' + "".join(
        f'<div class="hrow"><span>{label}</span><b class="{"ok" if ok else "no"}">{value}</b></div>' for label, value, ok in rows) + "</div>"
