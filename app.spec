pyinstaller --onefile --name MyApp ^
  --collect-all streamlit --copy-metadata streamlit ^
  --add-data "streamlit_app;streamlit_app" ^
  --add-data ".streamlit;.streamlit" ^
  --add-data "dashboard/static;dashboard/static" ^
  launcher.py
