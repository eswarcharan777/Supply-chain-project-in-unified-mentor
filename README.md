# APL Logistics Delivery Performance Dashboard

An interactive Streamlit dashboard that measures delivery performance, identifies delay-risk patterns, compares shipping modes, and highlights regional logistics bottlenecks.

## Project objective

Convert raw global supply-chain shipment records into operational decisions. The dashboard answers where delays occur, which shipping modes perform poorly, and which regions need attention.

## Dashboard modules

- Delivery-performance KPI overview
- Delivery delay-gap and source-risk analysis
- Shipping-mode comparison
- Regional, market, and country risk diagnostics
- Geographic delay-risk map
- Regional volume-versus-risk priority matrix
- Filtered-data CSV export and decision-ready insights
- Evidence-based operational recommendations and metric definitions
- Historical machine-learning delay-risk prediction
- Role-based dashboard access for Viewer, Analyst, and Admin users
- Local SQLite live-data store and FastAPI integration endpoints
- Clearly labeled customer-coordinate route-planning simulator

## Day 1 outputs

- `data/processed/cleaned_logistics.csv` — validated analytics-ready dataset
- `data/processed/day1_summary.json` — data audit and top-level KPIs
- `data/processed/data_quality_profile.csv` — missing-value and cardinality audit for dashboard fields
- `data/processed/*_performance.csv` — performance summaries by shipping mode, region, and customer segment
- `notebooks/day1_eda.ipynb` — reproducible exploratory analysis

## Project architecture

```text
APL_Logistics.csv
    -> Python data-cleaning pipeline
    -> cleaned_logistics.csv
    -> KPI/grouping functions
    -> Streamlit dashboard
    -> stakeholder insights and exportable filtered data
```

## Tech stack

- Python
- Streamlit
- Pandas
- Altair
- Scikit-learn
- SQLite
- FastAPI
- Uvicorn

## Project structure

```text
app.py                 # Streamlit dashboard
api.py                 # FastAPI application
src/                   # Data processing, metrics, authentication, ML, routing, and database modules
data/processed/        # Cleaned dataset and analysis outputs
tests/                 # Automated tests
deliverables/          # Research paper and executive summary
screenshots/           # Final project evidence screenshots
```

## Run the data pipeline

```powershell
& 'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' run_day1.py --source 'C:\Users\ASUS\Downloads\APL_Logistics.csv'
```

## Core business rule

`delivery_delay_gap = Days for shipping (real) - Days for shipment (scheduled)`

- Negative: Early
- Zero: On Time
- Positive: Delayed

## Run the dashboard

After running the Day 1 pipeline, start the Streamlit application:

```powershell
& 'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' -m streamlit run app.py
```

For a generic setup, install the project dependencies and start Streamlit with:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Live dashboard

[Open the deployed Streamlit dashboard](https://eswarcharan777-supply-chain-project-in-unified-mento-app-cmdjcl.streamlit.app/)

## Screenshots and demo

- Final dashboard evidence is available in the [`screenshots/`](screenshots/) folder.
- The project demo video will be added to the final submission package.

## Access roles

The current authentication module is a **local demonstration** and must be replaced with managed identity before public deployment.

- `viewer` / `viewer123` — dashboard overview only
- `analyst` / `analyst123` — overview, filtered-data export, delay prediction, and planning simulator
- `admin` / `admin123` — all Analyst access plus live-database refresh

## Live database API

The app can create a local SQLite database from the prepared dataset. Start the local API with:

```powershell
& 'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' -m uvicorn api:app --reload
```

Available endpoints:

- `GET /health` — database readiness and row count
- `GET /summary` — delivery summary from SQLite
- `GET /shipments?limit=100&shipping_mode=Standard%20Class` — non-personal operational shipment fields

## Upgrade scope and limitations

- The delay-risk model predicts a historical delayed-delivery label using fields available before delivery. It is an operational prioritization aid, not an automated decision system or a guarantee.
- The route planner is a nearest-neighbour planning simulator based on customer coordinates. The supplied dataset does not include warehouse origins, road network, traffic, carrier-cost, or service-time data, so it is not a real navigation or cost-optimization engine.
- SQLite and FastAPI are local development components. A production deployment needs managed authentication, secret storage, database backups, HTTPS, rate limiting, and an externally hosted database.

## Run verification tests

The Day 8 test suite validates cleaning rules, KPIs, grouped performance, default dashboard rendering, sidebar filters, the clear-all control, and a narrow real-data filter case.

```powershell
& 'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' -m unittest discover -s tests -v
```

## Validation completed

- 180,519 valid analysis rows are retained from the supplied CSV.
- Delivery performance is calculated from actual minus scheduled shipping days.
- Dashboard filters, default rendering, and a shipping-mode filter state are covered by automated Streamlit render tests.
- `Late_delivery_risk` is displayed separately from the calculated delay rate because their definitions differ in the source data.

## Known scope limits

- The supplied dataset has no order or delivery date field; date-range filtering is intentionally excluded.
- This project is diagnostic analytics. Predicting future delays and optimizing routes are future extensions, not claimed features.
