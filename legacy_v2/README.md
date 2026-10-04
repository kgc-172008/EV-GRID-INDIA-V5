# EV-GRID INDIA v2

Competition-oriented prototype for EV charging gap analysis and future charging planning.

## Run in VS Code
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

Use **Streamlit**, not the normal VS Code "Run Python File" button.

## Real data
Copy cleaned files into `data/`:
- `vehicle_registrations.csv`
- `chargers.csv`

Templates are in `data/real_data_templates/`.

The app remains usable offline in DEMO/SYNTHETIC mode.
