# QIMA RPA dashboard

A web dashboard that runs your existing `main.py` on a server, so you no longer run it from your own machine.

## Set up

1. `automation/main.py` is your script with three small fixes (see "Changes to main.py"). Add any helper `.py` files you use.
   Leave out `.env`, `input/` and `logs/`.
2. Copy `.env.example` to `.env` and set `DASH_PASSWORD` (and `TZ`, e.g. `Asia/Phnom_Penh`).
3. Start it:
   ```
   docker compose up -d --build
   ```
4. Open `http://<server>:8000`, sign in, then go to **Settings** and add your portal variables
   (`QIMA_USER` and `QIMA_PASS` are required). Save.
5. Click **Start a new run** and upload `booking.xlsx`, `booking_list.xlsx` and the PO PDFs.

Without Docker (Windows PowerShell), in the same virtual environment you use for main.py:
```
pip install fastapi "uvicorn[standard]" python-multipart
$env:DASH_PASSWORD="choose-a-password"
python -m uvicorn dashboard.app:app --port 8000
```
Then open http://localhost:8000. The dashboard only runs while this PC and window stay on.

## How it works

Each run gets its own folder under `/data/runs/<id>/` with a copy of `automation/`, your uploaded `input/`
files, a `.env` built from Settings, and an empty `logs/`. The dashboard runs `python main.py` there
and streams its output.

- **Progress steps** come from the screenshot names your script already saves in `logs/`
  (`login_page`, `booking_form`, `supplier_popup`, `excel_uploaded`, `po_all_done`, `inspection_details`...).
  No change to `main.py` is needed. If you rename screenshots, edit `STEPS` at the top of `dashboard/app.py`.
- **Uploads** are saved as `input/booking.xlsx`, `input/booking_list.xlsx` and `input/po_pdf/*.pdf`,
  the same layout as your project. Empty upload slots reuse the original files from the previous run.
- **Retry and Schedule** reuse the previous run's files, including its `booking_list.xlsx` with the Status column the
  script wrote back. Rows already marked DONE are skipped, so nothing is booked twice. Upload a new `booking_list.xlsx` to start fresh.
- **Failed** means the script crashed, timed out, or every booking failed. If only some bookings failed the run shows
  Done with a warning, the Bookings table shows which rows failed, and an alert is still sent.
- Only one run executes at a time. Others wait in the queue.
- **Schedule** starts a run at the chosen time on selected days, reusing the latest run's input files.
- Browser: runs headless by default (`HEADLESS=true` is passed to `main.py`). Choosing "Visible" in Settings runs it on a virtual display (xvfb).

## Security

Put the dashboard behind HTTPS (Caddy, Nginx or your host's built-in TLS) and set `COOKIE_SECURE=1`.
Portal credentials are stored in `/data/settings.json` on the server (file mode 600) and are never sent back to the browser.

## Changes to main.py

1. `DRY_RUN` mode called `input()` to wait for Enter. On a server there is no keyboard, so it raised an error and
   overwrote DRYRUN_OK with FAILED. It now only pauses when run from a terminal.
2. Paths in the `Booking Excel` and `PO PDF Folder` columns are normalised, so Windows-style paths such as
   `input\\po_pdf` or `C:\\...` fall back to the uploaded files instead of failing on Linux.
3. Nothing else changed. Your selectors and flow are untouched.

`booking_list.xlsx` must keep its `Bookings` sheet. Dry run is a Settings toggle (off by default in the dashboard).
