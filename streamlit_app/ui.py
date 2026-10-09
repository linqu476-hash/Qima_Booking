"""Design system for the QIMA booking desk: flat paper surfaces, ink type, one cobalt action colour,
and a checkpoint rail as the signature element."""
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=Figtree:wght@400;500;600;700&display=swap');
:root { --ink:#17153b; --bg:#f4f5fd; --paper:#fff; --line:#e0e3f3; --muted:#5f6488;
  --indigo:#5b4bdb; --sky:#1f8fff; --teal:#0fb5a6; --green:#1fb26b; --amber:#ffa91f; --coral:#ff5d5d; --pink:#e6409b; }
html, body, [class*="css"], .stMarkdown, button, input, textarea { font-family:'Figtree', system-ui, sans-serif !important; }
h1, h2, h3, .hero h1, .sec, .kpi b, .guide b, .guide em, .ins b { font-family:'Bricolage Grotesque', 'Figtree', sans-serif !important; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility:hidden; }
.stApp { background:radial-gradient(900px 420px at 100% 0%, rgba(31,143,255,.10), transparent 60%), radial-gradient(800px 400px at 0% 100%, rgba(230,64,155,.07), transparent 60%), var(--bg); color:var(--ink); }
.block-container { padding-top:3rem; max-width:1240px; }
:focus-visible { outline:2px solid var(--indigo) !important; outline-offset:2px; }
/* sidebar */
[data-testid="stSidebar"] { background:linear-gradient(190deg, #1b1650 0%, #3a2aa8 55%, #0a7f8c 100%); }
[data-testid="stSidebar"] * { color:#e4e6ff; }
[data-testid="stSidebarNav"]::before { content:"QIMA booking desk"; display:block; margin:10px 14px 18px; padding-bottom:14px; border-bottom:1px solid rgba(255,255,255,.18); font:800 1.2rem 'Bricolage Grotesque', sans-serif; color:#fff; }
[data-testid="stSidebarNav"] a { border-radius:10px; margin:3px 8px; padding:7px 10px; }
[data-testid="stSidebarNav"] a:hover { background:rgba(255,255,255,.12); }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:linear-gradient(90deg, var(--pink), var(--amber)); box-shadow:0 6px 16px rgba(230,64,155,.35); }
[data-testid="stSidebarNav"] a[aria-current="page"] * { color:#fff; font-weight:700; }
[data-testid="stSidebar"] button { background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.3); border-radius:10px; }
/* page banner */
.hero { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; padding:26px 30px; margin-bottom:22px; border-radius:20px; color:#fff;
  background:radial-gradient(circle at 92% 20%, rgba(255,169,31,.55), transparent 32%), radial-gradient(circle at 75% 120%, rgba(230,64,155,.6), transparent 42%), linear-gradient(115deg, #3a2aa8 0%, #1f8fff 60%, #0fb5a6 100%); box-shadow:0 16px 36px rgba(58,42,168,.28); }
.hero h1 { margin:0; padding:0; font-size:2.1rem; font-weight:800; letter-spacing:-.02em; line-height:1.1; color:#fff; }
.hero p { margin:6px 0 0; color:#e8eaff; max-width:60ch; }
.hero.compact { padding:20px 26px; } .hero.compact h1 { font-size:1.65rem; }
.chip { display:inline-flex; align-items:center; gap:8px; padding:8px 16px; border-radius:99px; background:rgba(255,255,255,.2); border:1px solid rgba(255,255,255,.4); font-weight:700; font-size:.88rem; backdrop-filter:blur(6px); color:#fff; }
.chip .dot { width:9px; height:9px; border-radius:50%; background:#cbd0ff; }
.chip.run .dot { background:var(--amber); animation:pulse 1.3s infinite; } .chip.ok .dot { background:#4ff0a4; } .chip.bad .dot { background:var(--coral); }
@keyframes pulse { 50% { opacity:.25; } }
@media (prefers-reduced-motion: reduce) { .chip.run .dot, .st.active i { animation:none !important; } }
/* sections and surfaces */
.sec { font-size:1.15rem; font-weight:700; margin:24px 0 12px; display:flex; align-items:center; gap:10px; }
.sec::before { content:""; width:6px; height:22px; border-radius:3px; background:linear-gradient(var(--indigo), var(--pink)); }
.sec small { font:500 .88rem 'Figtree', sans-serif; color:var(--muted); }
.card, [data-testid="stVerticalBlockBorderWrapper"] { background:var(--paper); border:1px solid var(--line); border-radius:16px; box-shadow:0 4px 14px rgba(58,42,168,.07); }
.card { padding:6px 18px; margin:0 0 14px; }
.slot { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.slot .n { width:30px; height:30px; border-radius:10px; display:grid; place-items:center; color:#fff; font-weight:800; flex:none; box-shadow:0 4px 10px rgba(23,21,59,.18); }
.slot b { display:block; line-height:1.2; } .slot small { color:var(--muted); }
/* KPI tiles: one hue each */
.kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:14px; margin:6px 0 20px; }
.kpi { --c:var(--indigo); position:relative; padding:16px 18px 14px; border-radius:16px; border:1px solid var(--line); overflow:hidden;
  background:linear-gradient(160deg, color-mix(in srgb, var(--c) 14%, #fff), #fff 70%); box-shadow:0 4px 14px rgba(58,42,168,.07); }
.kpi::before { content:""; position:absolute; inset:0 0 auto 0; height:5px; background:var(--c); }
.kpi small { display:block; color:var(--muted); font-weight:600; }
.kpi b { font-size:2rem; font-weight:800; line-height:1.15; letter-spacing:-.02em; color:var(--c); }
.kpi.info { --c:var(--indigo); } .kpi.sky { --c:var(--sky); } .kpi.ok { --c:var(--green); } .kpi.bad { --c:var(--coral); }
.kpi.warn { --c:var(--amber); } .kpi.teal { --c:var(--teal); } .kpi.pink { --c:var(--pink); }
/* checkpoint rail */
.rail { display:flex; margin:6px 0 20px; background:var(--paper); border:1px solid var(--line); border-radius:16px; padding:20px 12px 14px; overflow-x:auto; box-shadow:0 4px 14px rgba(58,42,168,.07); }
.st { flex:1; min-width:84px; text-align:center; position:relative; font-size:.84rem; color:var(--muted); }
.st i { display:inline-grid; place-items:center; width:30px; height:30px; border-radius:50%; border:2px solid var(--line); background:var(--paper); font-style:normal; font-weight:800; font-size:.8rem; position:relative; z-index:1; }
.st::before { content:""; position:absolute; top:14px; left:-50%; width:100%; height:3px; background:var(--line); }
.st:first-child::before { display:none; } .st span { display:block; margin-top:7px; }
.st.done i { background:linear-gradient(135deg, var(--green), var(--teal)); border-color:transparent; color:#fff; } .st.done::before { background:linear-gradient(90deg, var(--teal), var(--green)); } .st.done { color:var(--ink); }
.st.active i { background:linear-gradient(135deg, var(--amber), var(--pink)); border-color:transparent; color:#fff; box-shadow:0 0 0 5px rgba(255,169,31,.25); animation:pulse 1.3s infinite; } .st.active::before { background:linear-gradient(90deg, var(--green), var(--amber)); } .st.active { color:var(--ink); font-weight:700; }
.st.failed i { background:var(--coral); border-color:transparent; color:#fff; } .st.failed::before { background:var(--green); } .st.failed { color:#c43030; font-weight:700; }
.st.stopped i { background:var(--muted); border-color:transparent; color:#fff; }
/* insights panel */
.ins { display:flex; gap:22px; align-items:center; flex-wrap:wrap; background:var(--paper); border:1px solid var(--line); border-radius:16px; padding:18px 22px; margin:0 0 18px; box-shadow:0 4px 14px rgba(58,42,168,.07); }
.ring { --p:0; --c:var(--green); width:104px; height:104px; border-radius:50%; flex:none; display:grid; place-items:center; background:conic-gradient(var(--c) calc(var(--p) * 1%), #e6e8f8 0); }
.ring span { width:78px; height:78px; border-radius:50%; background:#fff; display:grid; place-items:center; font:800 1.35rem 'Bricolage Grotesque', sans-serif; color:var(--ink); }
.ins ul { margin:0; padding:0; list-style:none; flex:1; min-width:240px; } .ins li { padding:5px 0 5px 22px; position:relative; }
.ins li::before { content:""; position:absolute; left:0; top:12px; width:10px; height:10px; border-radius:50%; background:var(--c, var(--indigo)); }
.ins li.ok { --c:var(--green); } .ins li.warn { --c:var(--amber); } .ins li.bad { --c:var(--coral); } .ins li.info { --c:var(--sky); }
/* status pieces */
.po { display:inline-block; padding:3px 11px; margin:3px 4px 3px 0; border-radius:99px; font-size:.82rem; font-weight:700; }
.po.ok { background:#d8f6e7; color:#0a6b3f; } .po.no { background:#ffe0e0; color:#a52424; }
.note { padding:11px 15px; border-radius:12px; margin:6px 0 12px; font-weight:500; border-left:5px solid; }
.note.bad { background:#ffe6e6; color:#a52424; border-color:var(--coral); } .note.warn { background:#fff1d6; color:#7a4a00; border-color:var(--amber); }
.hrow { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #eceefb; font-size:.9rem; } .hrow:last-child { border:0; }
.hrow b { padding:2px 10px; border-radius:99px; font-size:.78rem; } .hrow b.ok { background:#d8f6e7; color:#0a6b3f; } .hrow b.no { background:#ffe0e0; color:#a52424; }
.guide { display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:14px; margin:6px 0 18px; }
.guide div { border-radius:16px; padding:18px 20px; color:#fff; box-shadow:0 10px 22px rgba(23,21,59,.16); }
.guide div:nth-child(1) { background:linear-gradient(135deg, var(--indigo), var(--sky)); } .guide div:nth-child(2) { background:linear-gradient(135deg, var(--teal), var(--green)); } .guide div:nth-child(3) { background:linear-gradient(135deg, var(--amber), var(--pink)); }
.guide em { font-style:normal; font-weight:800; font-size:1.6rem; opacity:.85; } .guide b { display:block; font-size:1.05rem; margin:4px 0 2px; } .guide span { opacity:.92; font-size:.9rem; }
/* controls */
[class*="st-key-stop_"] button { background:linear-gradient(135deg, #ff5d5d, #d62e4f) !important; color:#fff !important; border:0 !important; font-weight:700; box-shadow:0 8px 18px rgba(214,46,79,.35); }
.stButton > button, .stDownloadButton > button { border-radius:12px; font-weight:600; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg, var(--indigo), var(--pink)); border:0; color:#fff; box-shadow:0 8px 18px rgba(91,75,219,.35); transition:transform .15s; }
.stButton > button[kind="primary"]:hover { transform:translateY(-1px); }
[data-testid="stFileUploader"] section { border-radius:12px; border:1.5px dashed #a9a2f0; background:#f8f7ff; }
.stTabs [data-baseweb="tab-list"] { gap:6px; }
.stTabs [data-baseweb="tab"] { font-weight:600; background:var(--paper); border-radius:99px; padding:8px 18px; border:1px solid var(--line); }
.stTabs [aria-selected="true"] { background:linear-gradient(135deg, var(--indigo), var(--sky)); color:#fff; border-color:transparent; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }
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


def slot_head(n, title, hint, color="#5b4bdb"):
    return f'<div class="slot"><div class="n" style="background:{color}">{n}</div><div><b>{title}</b><small>{hint}</small></div></div>'


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


def insights(pct, lines):
    """Success-rate ring plus plain-language observations: [(kind, text)] with kind ok/warn/bad/info."""
    c = "var(--green)" if pct >= 90 else ("var(--amber)" if pct >= 60 else "var(--coral)")
    ring = f'<div class="ring" style="--p:{pct};--c:{c}"><span>{pct}%</span></div>'
    return f'<div class="ins">{ring}<ul>' + "".join(f'<li class="{k}">{t}</li>' for k, t in lines) + "</ul></div>"
