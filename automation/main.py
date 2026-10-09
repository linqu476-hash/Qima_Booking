"""
QIMA booking RPA  -  Playwright (Python)
Flow: Login -> Book now -> Product inspection -> General information
      (ref, supplier, date, time, Excel) -> Next -> Product information (PO PDFs)

Run:  python main.py
"""
import os, re, sys, time, logging, json
from datetime import datetime, date, time as dtime
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout, Page

load_dotenv()
BASE = Path(__file__).parent
URL = "https://www.qima.com/"
LOGIN_URL = "https://my.qima.com/"
TIMEOUT = 30_000

DEFAULTS = {"EXCEL_FILE": "input/booking.xlsx", "PO_PDF_DIR": "input/po_pdf"}
cfg = {k: os.getenv(k) or DEFAULTS.get(k, "") for k in (
    "QIMA_USER", "QIMA_PASS", "BOOKING_REF", "SUPPLIER_NAME",
    "START_DATE", "START_TIME", "EXCEL_FILE", "PO_PDF_DIR")}
JOB_FILE = BASE / (os.getenv("JOB_FILE") or "input/booking_list.xlsx")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

(BASE / "logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(BASE / "logs/run.log", encoding="utf-8"),
              logging.StreamHandler(sys.stdout)])
log = logging.getLogger("qima")


# ---------- helpers ----------
def shot(page: Page, name: str):
    p = BASE / "logs" / f"{time.strftime('%H%M%S')}_{name}.png"
    page.screenshot(path=str(p), full_page=True)
    log.info("screenshot -> %s", p.name)


def first_visible(page: Page, candidates, timeout=TIMEOUT):
    """Try several locators; return the first that becomes visible."""
    end = time.time() + timeout / 1000
    while time.time() < end:
        for loc in candidates:
            try:
                if loc.first.is_visible():
                    return loc.first
            except Exception:
                pass
        page.wait_for_timeout(300)
    raise PWTimeout(f"None of {len(candidates)} locators became visible")


def click_text(page: Page, text: str):
    loc = first_visible(page, [
        page.get_by_role("button", name=text),
        page.get_by_role("link", name=text),
        page.get_by_text(text, exact=True),
    ])
    loc.click()
    log.info("clicked '%s'", text)


def fill_field(page: Page, label: str, value: str):
    loc = first_visible(page, [
        page.get_by_label(label, exact=False),
        page.get_by_placeholder(label, exact=False),
        page.locator(f"xpath=//label[contains(.,'{label}')]/following::input[1]"),
    ])
    loc.click()
    loc.fill("")
    loc.fill(value)
    log.info("filled %s = %s", label, value)


# ---------- booking list (Excel) ----------
JOB_COLS = ["Booking Ref No.", "Starting Date", "Starting Time", "Supplier",
            "Booking Excel", "PO PDF Folder", "Status", "Message", "Updated"]


def fmt_ref(v) -> str:
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def fmt_date(v) -> str:
    """-> '11-Oct-2026' (QIMA format) from Excel date or text."""
    if isinstance(v, (datetime, date)):
        return v.strftime("%d-%b-%Y")
    t = str(v).strip()
    for f in ("%d-%b-%Y", "%d-%B-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(t, f).strftime("%d-%b-%Y")
        except ValueError:
            pass
    raise ValueError(f"Starting Date not readable: {v!r} (use e.g. 11-Oct-2026)")


def fmt_time(v) -> str:
    """-> '11:30' from Excel time / fraction of day / text."""
    if isinstance(v, (datetime, dtime)):
        return v.strftime("%H:%M")
    if isinstance(v, (int, float)):
        mins = round(float(v) * 24 * 60)
        return f"{(mins // 60) % 24:02d}:{mins % 60:02d}"
    m = re.match(r"^\s*(\d{1,2})[:.](\d{2})", str(v))
    if not m:
        raise ValueError(f"Starting Time not readable: {v!r} (use e.g. 11:30)")
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def load_jobs():
    if not JOB_FILE.exists():
        sys.exit(f"Booking list not found: {JOB_FILE}")
    ws = load_workbook(JOB_FILE)["Bookings"]
    head = {str(c.value).strip().lower(): i for i, c in enumerate(ws[1]) if c.value}
    missing = [c for c in JOB_COLS[:2] if c.lower() not in head]
    if missing:
        sys.exit(f"Missing column(s) in {JOB_FILE.name}: {missing}")
    jobs = []
    for r in range(2, ws.max_row + 1):
        def val(col):
            i = head.get(col.lower())
            return ws.cell(row=r, column=i + 1).value if i is not None else None
        ref = val("Booking Ref No.")
        if ref in (None, ""):
            continue
        status = str(val("Status") or "").strip().upper()
        if status == "DONE":
            continue
        jobs.append({"row": r, "ref": fmt_ref(ref), "date_raw": val("Starting Date"),
                     "time_raw": val("Starting Time"),
                     "supplier": str(val("Supplier") or "").strip(),
                     "excel": str(val("Booking Excel") or "").strip(),
                     "pdf_dir": str(val("PO PDF Folder") or "").strip()})
    return jobs


def save_status(row: int, status: str, message: str = ""):
    """Write Status / Message / Updated back to the booking list (file must be CLOSED in Excel)."""
    try:
        wb = load_workbook(JOB_FILE)
        ws = wb["Bookings"]
        head = {str(c.value).strip().lower(): i + 1 for i, c in enumerate(ws[1]) if c.value}
        for col, v in (("Status", status), ("Message", message[:300]),
                       ("Updated", time.strftime("%Y-%m-%d %H:%M:%S"))):
            if col.lower() in head:
                ws.cell(row=row, column=head[col.lower()], value=v)
        color = {"DONE": "C6EFCE", "FAILED": "FFC7CE", "DRYRUN_OK": "FFEB9C"}.get(status)
        if color and "status" in head:
            ws.cell(row=row, column=head["status"]).fill = PatternFill("solid", fgColor=color)
        wb.save(JOB_FILE)
    except PermissionError:
        log.warning("Cannot write status - close %s in Excel! (row %d = %s)", JOB_FILE.name, row, status)
    except Exception as e:
        log.warning("Cannot write status for row %d: %s", row, e)


def save_links(page, ref):
    """Remember the QIMA page reached, so the dashboard can show an Open link."""
    try:
        urls = []
        for u in [page.url] + [f.url for f in page.frames]:
            if u and u.startswith("http") and u not in urls:
                urls.append(u)
        p = BASE / "logs" / "result_links.json"
        data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
        data.append({"ref": str(ref), "title": page.title(), "urls": urls})
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("LINK booking %s -> %s", ref, urls)
    except Exception as e:
        log.warning("could not save link: %s", e)


def prepare_job(job):
    """Validate one row, fill cfg used by the steps; return (excel_path, pdfs)."""
    cfg["BOOKING_REF"] = job["ref"]
    cfg["START_DATE"] = fmt_date(job["date_raw"])
    if job["time_raw"] not in (None, ""):
        cfg["START_TIME"] = fmt_time(job["time_raw"])
    elif not cfg.get("START_TIME"):
        raise ValueError("Starting Time empty in Excel and START_TIME missing in .env")
    cfg["SUPPLIER_NAME"] = job["supplier"] or os.getenv("SUPPLIER_NAME", "")
    if not cfg["SUPPLIER_NAME"]:
        raise ValueError("Supplier empty in Excel and SUPPLIER_NAME missing in .env")
    excel = resolve_input(job["excel"], os.getenv("EXCEL_FILE") or "input/booking.xlsx")
    pdf_dir = resolve_input(job["pdf_dir"], os.getenv("PO_PDF_DIR") or "input/po_pdf")
    cfg["PO_PDF_DIR"] = str(pdf_dir)
    if not excel.exists():
        raise FileNotFoundError(f"Booking Excel not found: {excel}")
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF in {pdf_dir}")
    return excel, pdfs


def resolve_input(raw: str, default: str) -> Path:
    """Paths typed in the Excel list may use Windows style (backslashes, C:\\...). Find the file on this machine."""
    raw = (raw or default).replace("\\", "/")
    p = Path(raw) if Path(raw).is_absolute() else BASE / raw
    for cand in (p, BASE / "input" / Path(raw).name, BASE / default):
        if cand.exists():
            return cand
    return p


def ti_excel_path():
    """Technical Sheet (TI) Excel that is attached in the Purchase order (PO) box after the PO PDFs.
    Default input/technical_info.xlsx, or set TI_EXCEL. Returns None when the file is not there."""
    p = resolve_input(os.getenv("TI_EXCEL") or "", "input/technical_info.xlsx")
    return p if p.exists() else None


def files_for_tab(files, ti, idx, total, mode):
    """Files to put in the PO box of tab idx (0-based). TI_UPLOAD=last (default): the TI Excel goes with the
    last PO tab only, so it is uploaded once after all PO PDFs. TI_UPLOAD=each: it goes with every PO tab."""
    attach = bool(ti) and (mode == "each" or idx == total - 1)
    return list(files) + ([ti] if attach else []), attach


def check_env():
    for k in ("QIMA_USER", "QIMA_PASS"):
        if not cfg[k]:
            sys.exit(f"Missing {k} in .env")


# ---------- steps ----------
def find_in_frames(page: Page, builders, timeout=60_000):
    """Look for an element in the page AND all iframes. builders = list of fn(frame)->locator"""
    end = time.time() + timeout / 1000
    while time.time() < end:
        for fr in page.frames:
            for b in builders:
                try:
                    loc = b(fr)
                    if loc.count() and loc.first.is_visible():
                        return loc.first
                except Exception:
                    pass
        page.wait_for_timeout(500)
    raise PWTimeout("element not found in page or iframes")


def login(page: Page) -> Page:
    """Go directly to the portal login (www.qima.com 'Sign In' = https://my.qima.com/)."""
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    for txt in ("Accept", "Accept all", "Allow all"):      # cookie banner
        try:
            page.get_by_role("button", name=txt).first.click(timeout=1500)
            break
        except Exception:
            pass

    user = find_in_frames(page, [
        lambda f: f.get_by_placeholder("Enter your username"),
        lambda f: f.get_by_label("Username"),
        lambda f: f.locator("input[name='username'], input[id*='username' i], input[type='email']"),
    ], timeout=60_000)
    log.info("login page url: %s", page.url)
    shot(page, "login_page")

    pwd = find_in_frames(page, [
        lambda f: f.get_by_placeholder("Enter your password"),
        lambda f: f.get_by_label("Password"),
        lambda f: f.locator("input[type='password']"),
    ], timeout=15_000)

    user.fill(cfg["QIMA_USER"])
    pwd.fill(cfg["QIMA_PASS"])
    shot(page, "login_filled")

    btn = find_in_frames(page, [
        lambda f: f.get_by_role("button", name="Sign in", exact=True),
        lambda f: f.locator("button[type='submit']"),
    ], timeout=10_000)
    btn.click()

    # success = the dashboard 'Book Now' appears
    try:
        page.get_by_text("Overview", exact=True).first.wait_for(state="visible", timeout=60_000)
    except PWTimeout:
        shot(page, "login_failed")
        raise RuntimeError("Login failed or dashboard did not load - see logs/*_login_failed.png")
    page.wait_for_timeout(1500)
    log.info("login OK, url: %s", page.url)
    shot(page, "after_login")
    return page


def find_form_frame(page: Page, timeout=60_000, pattern=r"Booking Ref"):
    """Search ALL tabs and ALL iframes for the booking form (label 'Booking Ref')."""
    ctx = page.context
    end = time.time() + timeout / 1000
    while time.time() < end:
        for p in list(ctx.pages):
            for fr in p.frames:
                try:
                    loc = fr.get_by_text(re.compile(pattern, re.I))
                    if loc.count() and loc.first.is_visible():
                        return p, fr
                except Exception:
                    pass
        time.sleep(0.5)
    raise PWTimeout("Booking form (label 'Booking Ref') not found in any tab/iframe")


def open_product_inspection(page: Page) -> Page:
    """Dashboard -> Book Now -> Product Inspections -> Pre-Customs Clearance Inspection"""
    # 1) Book Now = FIRST icon of the left sidebar (sidebar may be collapsed: icons only)
    page.get_by_text("Overview", exact=True).first.wait_for(state="visible", timeout=45_000)
    page.wait_for_timeout(1500)
    clicked = False
    attempts = [
        lambda: page.get_by_text("Book Now", exact=True).first.click(timeout=3000),
        lambda: page.locator("[aria-label*='Book' i], [title*='Book' i]").first.click(timeout=3000),
        lambda: page.locator("aside a, aside button, nav a, nav button, [class*='sidebar' i] a, "
                             "[class*='sidebar' i] button, [class*='menu' i] a").first.click(timeout=3000),
        # last resort: the position of the first icon in the screenshot
        lambda: page.mouse.click(65, 113),
    ]
    for i, fn in enumerate(attempts, 1):
        try:
            fn()
            page.get_by_text("All services", exact=True).first.wait_for(state="visible", timeout=6000)
            clicked = True
            log.info("Book Now opened (method %d)", i)
            break
        except Exception:
            log.info("Book Now method %d did not open the panel", i)
    if not clicked:
        shot(page, "book_now_failed")
        raise RuntimeError("Could not open the Book Now panel - see logs/*_book_now_failed.png")

    # 2) wait for the 'All services' side panel to slide in
    page.get_by_text("All services", exact=True).first.wait_for(state="visible", timeout=20_000)
    page.wait_for_timeout(1000)               # slide animation
    shot(page, "all_services")

    # 3) Product Inspections (left list; already highlighted but click anyway)
    first_visible(page, [
        page.get_by_text("Product Inspections", exact=True),
        page.locator("text=Product Inspections"),
    ], timeout=15_000).click()
    log.info("clicked Product Inspections")
    page.wait_for_timeout(1000)

    # 4) Pre-Customs Clearance Inspection (PEO, right list)
    target = first_visible(page, [
        page.get_by_text("Pre-Customs Clearance Inspection", exact=True),
        page.locator("text=Pre-Customs Clearance Inspection"),
    ], timeout=15_000)
    target.scroll_into_view_if_needed()
    ctx = page.context
    n_before = len(ctx.pages)
    target.click()
    log.info("clicked Pre-Customs Clearance Inspection")

    # the form may open in a NEW TAB and/or inside an IFRAME -> search everywhere
    page.wait_for_timeout(2000)
    try:
        page, fr = find_form_frame(page, timeout=60_000)
    except PWTimeout:
        log.error("booking form not found. tabs:")
        for i, p in enumerate(ctx.pages):
            log.error("  tab %d: %s  frames=%d", i, p.url, len(p.frames))
        shot(page, "booking_form_missing")
        raise RuntimeError("Booking form did not open - see logs/*_booking_form_missing.png")
    page.bring_to_front()
    log.info("booking form found. url=%s  in iframe=%s", page.url, fr != page.main_frame)
    shot(page, "booking_form")
    return page


def after_label(page: Page, label: str, kinds="self::input or self::select or self::textarea"):
    """First form control that follows a text label (e.g. 'Booking Ref No.')."""
    return page.locator(
        f"xpath=(//*[starts-with(normalize-space(text()),'{label}')]"
        f"/following::*[{kinds}])[1]")


def label_box(page: Page, label: str):
    return page.locator(f"xpath=//*[starts-with(normalize-space(text()),'{label}')]").first


def general_information(page: Page, excel: Path):
    """Step 1 of 4: General Information (numbers = red numbers in the screenshot)."""
    page, fr = find_form_frame(page, timeout=30_000)      # form may be in an iframe
    page.wait_for_timeout(1000)

    # 1) Booking Ref No.  (3 ways, then verify the value)
    ref_val = cfg["BOOKING_REF"]
    candidates = [
        after_label(fr, "Booking Ref"),
        fr.get_by_label(re.compile("Booking Ref", re.I)),
        fr.locator("input[type='text']:visible, input:not([type]):visible").first,
    ]
    filled = False
    for c in candidates:
        try:
            c.first.wait_for(state="visible", timeout=6000)
            c.first.click()
            c.first.fill(ref_val)
            if c.first.input_value().strip() == ref_val:
                filled = True
                break
        except Exception:
            continue
    if not filled:                      # field is already focused in the screenshot -> just type
        page.keyboard.type(ref_val, delay=60)
    log.info("1) booking ref = %s (filled=%s)", ref_val, filled)
    shot(page, "booking_ref_done")

    # 2) Supplier: (1) Select or Add -> (2) click row -> (3) Select button
    name = cfg["SUPPLIER_NAME"]
    pat = re.compile(re.escape(name), re.I)
    fr.get_by_text("Select or Add", exact=True).first.click()
    fr.get_by_text("Select Supplier", exact=True).first.wait_for(state="visible", timeout=20_000)
    page.wait_for_timeout(1500)
    shot(page, "supplier_popup")

    # optional: filter with the Search box
    try:
        box = fr.get_by_placeholder("Search").first
        box.wait_for(state="visible", timeout=3000)
        box.fill(name)
        page.wait_for_timeout(1500)
    except Exception:
        pass

    # (2) the row, e.g. TRAXAPPAREL  (fallback: anything containing 'trax')
    row = None
    for p_ in (pat, re.compile("trax", re.I)):
        for loc in (fr.locator("tr", has_text=p_), fr.get_by_role("row", name=p_), fr.get_by_text(p_)):
            try:
                if loc.first.is_visible():
                    row = loc.first
                    break
            except Exception:
                pass
        if row:
            break
    if row is None:
        shot(page, "supplier_not_found")
        raise RuntimeError(f"Supplier '{name}' not found in the list - see logs/*_supplier_not_found.png")
    row.click()
    page.wait_for_timeout(800)
    shot(page, "supplier_row_selected")

    # (3) blue 'Select' button
    fr.get_by_role("button", name="Select", exact=True).first.click()
    fr.get_by_text("Select Supplier", exact=True).first.wait_for(state="hidden", timeout=15_000)
    log.info("2) supplier selected (%s)", name)
    page.wait_for_timeout(1500)
    shot(page, "supplier_done")

    # 3) Starting Date
    date_in = after_label(fr, "Starting Date")
    date_in.click()
    try:
        date_in.fill(cfg["START_DATE"])
    except Exception:
        page.keyboard.type(cfg["START_DATE"], delay=60)
    page.keyboard.press("Enter")
    label_box(fr, "Expected Dates").click()          # close the calendar
    log.info("3) starting date = %s", cfg["START_DATE"])
    page.wait_for_timeout(1000)

    # 4) Starting Time - masked HH:MM box. Clear it fully, type digits only, verify.
    t = cfg["START_TIME"]                       # e.g. "11:30"
    digits = t.replace(":", "")                 # "1130"
    tbox = after_label(fr, "Starting Time").first
    tbox.wait_for(state="visible", timeout=15_000)

    def read_time():
        try:
            return tbox.input_value().strip()
        except Exception:
            return ""

    def clear_time():
        tbox.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.keyboard.press("Delete")
        page.wait_for_timeout(300)

    strategies = [
        lambda: page.keyboard.type(digits, delay=120),   # mask inserts ':' itself
        lambda: page.keyboard.type(t, delay=120),        # plain with colon
        lambda: tbox.fill(t),                            # direct fill
        lambda: tbox.press_sequentially(t, delay=150),
    ]
    ok = False
    for i, st in enumerate(strategies, 1):
        try:
            clear_time()
            st()
            page.wait_for_timeout(500)
            if read_time() == t:
                ok = True
                log.info("4) starting time = %s (strategy %d)", t, i)
                break
            log.info("   time strategy %d gave '%s'", i, read_time())
        except Exception as e:
            log.info("   time strategy %d error: %s", i, e)
    page.keyboard.press("Tab")                  # leave the field -> validates
    page.wait_for_timeout(800)
    if not ok:
        shot(page, "time_failed")
        raise RuntimeError(f"Could not set Starting Time to {t}; field shows '{read_time()}' - see logs/*_time_failed.png")
    shot(page, "date_time_done")

    # 5) Excel file (hidden <input type=file> behind 'Drop file(s) here or browse')
    fin = fr.locator("input[type='file']").first
    fin.wait_for(state="attached", timeout=15_000)
    fin.set_input_files(str(excel))
    log.info("5) excel uploaded: %s", excel.name)
    page.wait_for_timeout(4000)
    shot(page, "excel_uploaded")

    # 6) Next
    nxt = fr.get_by_role("button", name="Next", exact=True).first
    nxt.scroll_into_view_if_needed()
    nxt.click()
    log.info("6) clicked Next")
    page.wait_for_load_state("networkidle", timeout=60_000)
    page.wait_for_timeout(3000)
    shot(page, "after_next")


def po_digits(text: str) -> str:
    return re.sub(r"\D", "", text or "")


def get_po_tabs(fr):
    """PO number tabs at the top of step 2 (row of '0902981089.' ... above 'Product Ref.')."""
    ref_y = None
    try:
        ref_y = fr.get_by_text(re.compile(r"Product Ref", re.I)).first.bounding_box()["y"]
    except Exception:
        pass
    loc = fr.get_by_text(re.compile(r"^\s*\d{8,}\.?\s*$"))
    tabs = []
    for i in range(loc.count()):
        el = loc.nth(i)
        try:
            bb = el.bounding_box()
            if bb and (ref_y is None or bb["y"] < ref_y):      # tabs are above the form; table cell is below
                tabs.append((el.inner_text().strip(), el))
        except Exception:
            pass
    return tabs


def pdfs_for_po(po: str, pdfs):
    d = po_digits(po)
    short = d.lstrip("0")
    return [p for p in pdfs if d in po_digits(p.name) or (short and short in po_digits(p.name))]


def product_information(page: Page, pdfs, ti=None):
    """Step 2 of 4: for every PO tab -> click tab -> upload matching PO pdf.
    After the last PO PDF the TI Excel is uploaded into the same Purchase order (PO) box."""
    page, fr = find_form_frame(page, timeout=60_000, pattern=r"Purchase order")
    page.wait_for_timeout(2000)
    shot(page, "product_info")

    po_list = [t for t, _ in get_po_tabs(fr)]
    log.info("found %d PO tab(s): %s", len(po_list), po_list)
    if not po_list:
        shot(page, "no_po_tabs")
        raise RuntimeError("No PO tabs found on Product Information - see logs/*_no_po_tabs.png")

    ti_mode = (os.getenv("TI_UPLOAD") or "last").strip().lower()
    if ti:
        log.info("TI Excel to attach: %s (mode=%s)", ti.name, ti_mode)
    uploaded, missing, failed = [], [], []
    for idx, po in enumerate(po_list):
        # re-find the tab each time (page re-renders after a click)
        tab = next((el for t, el in get_po_tabs(fr) if t == po), None)
        if tab is None:
            failed.append(po)
            continue
        tab.scroll_into_view_if_needed()
        tab.click()
        page.wait_for_timeout(1200)

        files = pdfs_for_po(po, pdfs)
        if not files:
            log.warning("PO %s: no matching PDF in %s", po, cfg["PO_PDF_DIR"])
            missing.append(po)
        to_upload, attach_ti = files_for_tab(files, ti, idx, len(po_list), ti_mode)
        if not to_upload:
            continue
        try:
            fin = fr.locator(
                "xpath=(//*[starts-with(normalize-space(text()),'Purchase order')]"
                "/following::input[@type='file'])[1]")
            if fin.count() == 0:
                fin = fr.locator("input[type='file']").last
            fin.wait_for(state="attached", timeout=15_000)
            fin.set_input_files([str(f) for f in to_upload])      # PDF(s) and, on the last tab, the TI Excel
            # verify the file name is shown
            fr.get_by_text(to_upload[0].name).first.wait_for(state="visible", timeout=20_000)
            log.info("PO %s <- %s", po, [f.name for f in to_upload])
            if attach_ti:
                try:
                    fr.get_by_text(ti.name).first.wait_for(state="visible", timeout=10_000)
                    log.info("TI Excel attached in the PO box of %s", po)
                except PWTimeout:
                    log.warning("TI Excel name not visible after upload on PO %s (long names may be shortened)", po)
                    shot(page, "ti_check")
            uploaded.append(po)
        except Exception as e:
            log.error("PO %s upload failed: %s", po, e)
            shot(page, f"po_fail_{po_digits(po)}")
            failed.append(po)
        page.wait_for_timeout(800)

    shot(page, "po_all_done")
    log.info("SUMMARY  uploaded=%d  no_pdf=%d  failed=%d", len(uploaded), len(missing), len(failed))
    if missing:
        log.warning("POs WITHOUT pdf: %s", missing)
    if failed:
        log.warning("POs FAILED: %s", failed)
    return page


def next_to_inspection_details(page: Page) -> Page:
    """Step 2 -> Step 3: click Next (bottom right) after all PO files are uploaded."""
    page, fr = find_form_frame(page, timeout=20_000, pattern=r"Purchase order")
    nxt = fr.get_by_role("button", name="Next", exact=True).first
    nxt.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    nxt.click()
    log.info("clicked Next (Product Information -> Inspection Details)")
    page.wait_for_load_state("networkidle", timeout=60_000)
    page.wait_for_timeout(3000)
    shot(page, "inspection_details")

    # still on step 2? -> validation error (e.g. a required file/field is missing)
    try:
        _, fr2 = find_form_frame(page, timeout=3000, pattern=r"Drop file")
        if fr2.get_by_text(re.compile(r"Purchase order \(PO\)", re.I)).first.is_visible():
            shot(page, "next_blocked")
            raise RuntimeError("Still on Product Information after Next - check logs/*_next_blocked.png "
                               "(a required field or file is probably missing)")
    except PWTimeout:
        pass                                    # form no longer there = moved to step 3
    log.info("now on step 3: Inspection Details")
    return page


def go_dashboard(ctx):
    """Back to the dashboard between bookings (close extra tabs, re-login if session ended)."""
    for p in ctx.pages[1:]:
        try:
            p.close()
        except Exception:
            pass
    page = ctx.pages[0]
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    try:
        page.get_by_text("Overview", exact=True).first.wait_for(state="visible", timeout=30_000)
    except PWTimeout:
        page = login(page)
    return page


def main():
    check_env()
    jobs = load_jobs()
    if not jobs:
        sys.exit(f"Nothing to do: no pending rows in {JOB_FILE.name} (DONE rows are skipped).")
    log.info("%d booking(s) to process from %s", len(jobs), JOB_FILE.name)

    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS, slow_mo=300)
        ctx = browser.new_context(viewport={"width": 1500, "height": 900})
        page = ctx.new_page()
        page.set_default_timeout(TIMEOUT)
        page.on("dialog", lambda d: d.accept())
        try:
            page = login(page)
            for n, job in enumerate(jobs, 1):
                log.info("===== booking %d/%d  ref=%s  (excel row %d) =====", n, len(jobs), job["ref"], job["row"])
                try:
                    excel, pdfs = prepare_job(job)
                    ti = ti_excel_path()
                    if not ti:
                        log.warning("No TI Excel found (input/technical_info.xlsx): continuing without it")
                    log.info("date=%s time=%s supplier=%s", cfg["START_DATE"], cfg["START_TIME"], cfg["SUPPLIER_NAME"])
                    page = open_product_inspection(page)
                    general_information(page, excel)
                    page = product_information(page, pdfs, ti)
                    page = next_to_inspection_details(page)
                    save_links(page, job["ref"])
                    # ---- step 3 (Inspection Details) / step 4 (Review) can be added here ----
                    if DRY_RUN:
                        save_status(job["row"], "DRYRUN_OK", "Reached Inspection Details (dry run, not submitted)")
                        results.append((job["ref"], "DRYRUN_OK"))
                        if sys.stdin and sys.stdin.isatty():   # only pause when a person is at the keyboard
                            input("DRY_RUN: check the browser, press Enter for the next booking...")
                    else:
                        save_status(job["row"], "DONE", "Reached Inspection Details")
                        results.append((job["ref"], "DONE"))
                except Exception as e:
                    log.exception("booking %s FAILED", job["ref"])
                    try:
                        shot(ctx.pages[-1], f"error_{job['ref']}")
                    except Exception:
                        pass
                    save_status(job["row"], "FAILED", str(e).splitlines()[0] if str(e) else repr(e))
                    results.append((job["ref"], "FAILED"))
                if n < len(jobs):
                    page = go_dashboard(ctx)
        finally:
            ctx.close()
            browser.close()

    log.info("========== SUMMARY ==========")
    for ref, st in results:
        log.info("%s  ->  %s", ref, st)


if __name__ == "__main__":
    main()
