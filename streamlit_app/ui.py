"""Design system for the QIMA booking desk: flat paper surfaces, ink type, one cobalt action colour,
and a checkpoint rail as the signature element."""
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=Figtree:wght@400;500;600;700&display=swap');
:root { --ink:#0e1b26; --mist:#eef1f0; --paper:#fff; --line:#d7dedb; --muted:#566772; --go:#0b8a5b; --wait:#b86e00; --stop:#c8372d; --sig:#2547d0; }
html, body, [class*="css"], .stMarkdown, button, input, textarea { font-family:'Figtree', system-ui, sans-serif !important; }
h1, h2, h3, .hero h1, .sec, .kpi b, .guide b { font-family:'Bricolage Grotesque', 'Figtree', sans-serif !important; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility:hidden; }
.stApp { background:var(--mist); color:var(--ink); }
.block-container { padding-top:3rem; max-width:1240px; }
:focus-visible { outline:2px solid var(--sig) !important; outline-offset:2px; }
/* sidebar */
[data-testid="stSidebar"] { background:var(--ink); }
[data-testid="stSidebar"] * { color:#cfdbe3; }
[data-testid="stSidebarNav"]::before { content:"QIMA booking desk"; display:block; margin:10px 14px 18px; padding-bottom:14px; border-bottom:1px solid rgba(255,255,255,.14);
  font:700 1.15rem 'Bricolage Grotesque', sans-serif; color:#fff; letter-spacing:-.01em; }
[data-testid="stSidebarNav"] a { border-radius:6px; margin:2px 8px; padding:6px 10px; border-left:3px solid transparent; }
[data-testid="stSidebarNav"] a:hover { background:rgba(255,255,255,.07); }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:rgba(255,255,255,.10); border-left-color:#5eead4; }
[data-testid="stSidebarNav"] a[aria-current="page"] * { color:#fff; font-weight:700; }
[data-testid="stSidebar"] button { background:transparent; border:1px solid rgba(255,255,255,.28); border-radius:6px; }
/* page header */
.hero { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap; padding:0 0 16px; margin-bottom:22px; border-bottom:2px solid var(--ink); }
.hero h1 { margin:0; padding:0; font-size:2.1rem; font-weight:800; letter-spacing:-.02em; line-height:1.1; color:var(--ink); }
.hero p { margin:6px 0 0; color:var(--muted); max-width:60ch; }
.hero.compact h1 { font-size:1.7rem; }
.chip { display:inline-flex; align-items:center; gap:8px; padding:6px 13px; border-radius:6px; border:1.5px solid currentColor; font-weight:700; font-size:.88rem; background:var(--paper); color:var(--muted); }
.chip .dot { width:8px; height:8px; border-radius:50%; background:currentColor; }
.chip.run { color:var(--wait); } .chip.run .dot { animation:pulse 1.3s infinite; } .chip.ok { color:var(--go); } .chip.bad { color:var(--stop); }
@keyframes pulse { 50% { opacity:.25; } }
@media (prefers-reduced-motion: reduce) { .chip.run .dot, .st.active i { animation:none !important; } }
/* sections and surfaces */
.sec { font-size:1.15rem; font-weight:700; margin:22px 0 10px; color:var(--ink); }
.sec small { font:500 .88rem 'Figtree', sans-serif; color:var(--muted); margin-left:10px; }
.card, [data-testid="stVerticalBlockBorderWrapper"] { background:var(--paper); border:1px solid var(--line); border-radius:8px; box-shadow:none; }
.card { padding:6px 18px; margin:0 0 14px; }
.slot { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.slot .n { width:26px; height:26px; border-radius:6px; display:grid; place-items:center; color:#fff; font-weight:700; font-size:.85rem; flex:none; background:var(--ink) !important; }
.slot b { display:block; line-height:1.2; } .slot small { color:var(--muted); }
/* KPI band: one joined strip instead of separate cards */
.kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); background:var(--paper); border:1px solid var(--line); border-radius:8px; margin:6px 0 20px; overflow:hidden; }
.kpi { padding:14px 18px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); margin:0 -1px -1px 0; }
.kpi small { display:block; color:var(--muted); font-weight:500; }
.kpi b { font-size:1.9rem; font-weight:700; line-height:1.15; letter-spacing:-.02em; }
.kpi.ok b { color:var(--go); } .kpi.bad b { color:var(--stop); } .kpi.warn b { color:var(--wait); }
/* checkpoint rail */
.rail { display:flex; gap:0; margin:6px 0 20px; background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:20px 12px 14px; overflow-x:auto; }
.st { flex:1; min-width:84px; text-align:center; position:relative; font-size:.84rem; color:var(--muted); }
.st i { display:inline-grid; place-items:center; width:26px; height:26px; border-radius:50%; border:2px solid var(--line); background:var(--paper); color:var(--muted); font-style:normal; font-weight:700; font-size:.78rem; position:relative; z-index:1; }
.st::before { content:""; position:absolute; top:12px; left:-50%; width:100%; height:2px; background:var(--line); }
.st:first-child::before { display:none; } .st span { display:block; margin-top:7px; }
.st.done i { background:var(--ink); border-color:var(--ink); color:#fff; } .st.done::before { background:var(--ink); } .st.done { color:var(--ink); }
.st.active i { border-color:var(--wait); color:var(--wait); box-shadow:0 0 0 4px rgba(184,110,0,.18); animation:pulse 1.3s infinite; } .st.active::before { background:linear-gradient(90deg, var(--ink), var(--wait)); } .st.active { color:var(--ink); font-weight:700; }
.st.failed i { background:var(--stop); border-color:var(--stop); color:#fff; } .st.failed::before { background:var(--ink); } .st.failed { color:var(--stop); font-weight:700; }
.st.stopped i { background:var(--muted); border-color:var(--muted); color:#fff; }
/* status pieces */
.po { display:inline-block; padding:2px 10px; margin:3px 4px 3px 0; border-radius:5px; font-size:.82rem; font-weight:600; border:1px solid; }
.po.ok { background:#e5f5ee; color:#075c3d; border-color:#a9dcc5; } .po.no { background:#fbe9e7; color:#8f2118; border-color:#efb4ae; }
.note { padding:10px 14px; border-radius:6px; margin:6px 0 12px; font-weight:500; border-left:4px solid; }
.note.bad { background:#fbe9e7; color:#8f2118; border-color:var(--stop); } .note.warn { background:#fdf1dc; color:#7a4800; border-color:var(--wait); }
.hrow { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid var(--mist); font-size:.9rem; } .hrow:last-child { border:0; }
.hrow b { font-size:.8rem; font-weight:700; } .hrow b.ok { color:var(--go); } .hrow b.no { color:var(--stop); }
.guide { display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:14px; margin:6px 0 18px; }
.guide div { background:var(--paper); border:1px solid var(--line); border-top:3px solid var(--ink); border-radius:8px; padding:16px 18px; }
.guide em { font:800 1.5rem 'Bricolage Grotesque', sans-serif; font-style:normal; color:var(--sig); } .guide b { display:block; font-size:1.05rem; margin:4px 0 2px; } .guide span { color:var(--muted); font-size:.9rem; }
/* controls */
.stButton > button, .stDownloadButton > button { border-radius:6px; font-weight:600; border:1px solid var(--ink); }
.stButton > button[kind="primary"] { background:var(--sig); border-color:var(--sig); color:#fff; box-shadow:none; }
.stButton > button[kind="primary"]:hover { background:#1b37a8; border-color:#1b37a8; }
[data-testid="stFileUploader"] section { border-radius:8px; border:1.5px dashed #9bacb5; background:#f9fbfa; }
.stTabs [data-baseweb="tab"] { font-weight:600; }
@media (max-width:700px) { .block-container { padding-top:2rem; } .hero h1 { font-size:1.6rem; } }
</style>
"""


def hero(title, subtitle, chip_text, chip_kind):
    return (f'<div class="hero"><div><h1>{title}</h1><p>{subtitle}</p></div>'
            f'<div class="chip {chip_kind}"><span class="dot"></span>{chip_text}</div></div>')


def head(title, subtitle, chip_text, chip_kind):
    return hero(title, subtitle, chip_text, chip_kind).replace('class="hero"', 'class="hero compact"', 1)


def kpis(items):
    return '<div class="kpis">' + "".join(
        f'<div class="kpi {k}"><small>{label}</small><b>{value}</b></div>' for label, value, k in items) + "</div>"


def slot_head(n, title, hint, color=None):
    return f'<div class="slot"><div class="n">{n}</div><div><b>{title}</b><small>{hint}</small></div></div>'


def guide():
    cards = [("1", "Upload files", "Add the Excel files and PO PDFs. Previews and PO coverage appear right away."),
             ("2", "Start the run", "Try a dry run first. It stops at Inspection Details and books nothing."),
             ("3", "Check results", "Follow each checkpoint live, then review statuses and screenshots.")]
    return '<div class="guide">' + "".join(f"<div><em>{n}</em><b>{t}</b><span>{d}</span></div>" for n, t, d in cards) + "</div>"


def rail(steps):
    parts = []
    for i, (label, s) in enumerate(steps, 1):
        mark = {"done": "&#10003;", "failed": "&#10005;", "stopped": "&#9632;"}.get(s, str(i))
        parts.append(f'<div class="st {s}"><i>{mark}</i><span>{label}</span></div>')
    return '<div class="rail">' + "".join(parts) + "</div>"


def po_chips(pairs):
    return "".join(f'<span class="po {"ok" if ok else "no"}">{po}</span>' for po, ok in pairs)


def health(rows):
    return '<div class="card">' + "".join(
        f'<div class="hrow"><span>{label}</span><b class="{"ok" if ok else "no"}">{value}</b></div>' for label, value, ok in rows) + "</div>"
