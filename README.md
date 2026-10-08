# QIMA RPA dashboard

A web dashboard that runs your existing `main.py` on a server, so you no longer run it from your own machine.

## Set up

1. Copy `main.py` (and any helper `.py` files) from your qima_rpa project into `automation/`.
   Leave out `.env`, `input/` and `logs/`.
2. Copy `.env.example` to `.env` and set `DASH_PASSWORD` (and `TZ`, e.g. `Asia/Phnom_Penh`).
3. Start it:
   ```
   docker compose up -d --build
   ```
4. Open `http://<server>:8000`, sign in, then go to **Settings** and add your portal variables
   (the names from your old `.env.example`, such as the username and password). Save.
5. Click **Start a new run** and upload `booking.xlsx`, `booking_list.xlsx` and the PO PDFs.

Without Docker: `pip install -r requirements.txt && playwright install chromium`, set `DASH_PASSWORD`,
then `uvicorn dashboard.app:app --port 8000`.

## How it works

Each run gets its own folder under `/data/runs/<id>/` with a copy of `automation/`, your uploaded `input/`
files, a `.env` built from Settings, and an empty `logs/`. The dashboard runs `python main.py` there
and streams its output.

- **Progress steps** come from the screenshot names your script already saves in `logs/`
  (`login_page`, `booking_form`, `supplier_popup`, `excel_uploaded`, `po_all_done`, `inspection_details`...).
  No change to `main.py` is needed. If you rename screenshots, edit `STEPS` at the top of `dashboard/app.py`.
- **Uploads** are saved as `input/booking.xlsx`, `input/booking_list.xlsx` and `input/po_pdf/*.pdf`,
  the same layout as your project. Empty upload slots reuse the original files from the previous run.
- **Retry** re-queues a run with the same original input files.
- **Failed** means the script exited with an error or timed out. A run that exits normally but saved
  `*_error.png` screenshots shows as Done with an error warning and still triggers an alert.
- Only one run executes at a time. Others wait in the queue.
- **Schedule** starts a run at the chosen time on selected days, reusing the latest run's input files.
- Browser: a virtual display (xvfb) is used, so scripts that open a visible browser work on the server too.
  `HEADLESS` is also passed as an environment variable if you want `main.py` to read it.

## Security

Put the dashboard behind HTTPS (Caddy, Nginx or your host's built-in TLS) and set `COOKIE_SECURE=1`.
Portal credentials are stored in `/data/settings.json` on the server (file mode 600) and are never sent back to the browser.
