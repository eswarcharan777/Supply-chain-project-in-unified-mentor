# Day 8 Testing Report

**Completed:** 25 October 2026

## Result

All nine automated tests passed.

## Data and KPI tests

1. Delivery categories correctly classify early, on-time, delayed, and missing values.
2. The preparation pipeline removes exact duplicate records and invalid shipping durations.
3. Missing required fields produce a clear error.
4. KPI calculations match known sample data.
5. Empty datasets return safe zero-valued KPIs.
6. Grouped performance and the data-quality profile return expected values.

## Dashboard tests

7. The default dashboard renders KPI cards, filters, download control, insights, and recommendations.
8. Selecting First Class returns 27,814 shipments and a 100.00% calculated delayed-delivery rate; Clear all filters restores 180,519 shipments.
9. The exact narrow filter case validates the manual dashboard result: First Class, Africa, North Africa, Argelia, and Consumer returns 30 shipments and a 100.00% calculated delayed-delivery rate.

## Command

```powershell
& 'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' -m unittest discover -s tests -v
```

For this Windows sandbox, set `TEMP` and `TMP` to the project's `.tmp-streamlit-test` folder before running dashboard tests if the default temporary directory is protected.
