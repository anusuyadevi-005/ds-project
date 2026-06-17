# AQI Explorer (Local)

## Files
- `site/index.html` - main UI
- `site/assets/app.js` - frontend logic
- `site/data/stations_geo.csv` - station-level data extracted from `AQI.csv`

## Run locally
Because browsers block loading local CSV files via `file://`, serve the `site/` directory.

### Option A: Python
```bash
cd site
python -m http.server 8000
```
Then open:
- http://localhost:8000

### Option B: VSCode Live Server
Open `site/index.html` and use **Go Live**.

## Notes
- Charts ignore missing numeric values (`NA`).
- Map uses OpenStreetMap tiles.

