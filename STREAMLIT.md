# Streamlit edition

Files: `streamlit_app/app.py` (main file), `streamlit_app/core.py`, `streamlit_app/requirements.txt`,
`streamlit_app/packages.txt`, `.streamlit/secrets.toml.example`. It reuses `automation/main.py` unchanged.

Deploy on Streamlit Community Cloud:
1. share.streamlit.io, sign in with GitHub, Create app.
2. Repository `linqu476-hash/Qima_Booking`, branch `main`, main file path `streamlit_app/app.py`.
3. Advanced settings: Python 3.12, and paste the Secrets from `.streamlit/secrets.toml.example` with your real values.
4. Deploy. The first start installs the browser and takes a few minutes.

Run it locally instead:
    pip install -r streamlit_app/requirements.txt
    python -m playwright install chromium
    copy .streamlit\secrets.toml.example .streamlit\secrets.toml   (then edit it)
    streamlit run streamlit_app/app.py
Limits: storage is wiped on restart or sleep, one run at a time, no scheduler or alerts.
