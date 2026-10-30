# Day 8 Testing Report

**Completed:** 25 October 2026
**Updated:** 30 October 2026

## Result

All 16 automated tests pass.

## Data and KPI tests

1. Delivery categories correctly classify early, on-time, delayed, and missing values.
2. The preparation pipeline removes exact duplicate records and invalid shipping durations.
3. Missing required fields produce a clear error.
4. KPI calculations match known sample data.
5. Empty datasets return safe zero-valued KPIs.
6. Grouped performance and the data-quality profile return expected values.

## Filter tests

7. Market selection restricts the available regions and countries.
8. Downstream selections that are no longer valid after an upstream change are removed.

## Dashboard render tests

9. The default dashboard renders the filter controls and waits for a filter selection.
10. Selecting First Class returns 27,814 shipments and a 100.00% calculated delayed-delivery rate.
11. Clear all filters returns to the filter prompt and resets every filter widget.
12. The exact narrow filter case validates the manual dashboard result: First Class, Africa, North Africa, Argelia, and Consumer returns 30 shipments and a 100.00% calculated delayed-delivery rate.
13. The route-planning simulator generates a visit plan and distance metric without raising an error.

## Route simulation unit tests

14. A plan is built when the `Order City` column is present.
15. A plan is built when the `Order City` column is absent, which is the case for the dashboard's own column set.
16. Nearest-neighbour ordering is respected and rows without coordinates are ignored.

## Command

```powershell
& 'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' -m unittest discover -s tests -v
```

For this Windows sandbox, set `TEMP` and `TMP` to the project's `.tmp-streamlit-test` folder before running dashboard tests if the default temporary directory is protected.

## Defects found and fixed in this review

1. **Clear all filters crashed the app.** The control reset `prepare_export`, a checkbox, to a list value. Streamlit raised `TypeError: 'list' object cannot be interpreted as an integer` and the dashboard stopped rendering. The export toggle is now reset to its boolean value.
2. **The clear-all test was clicking the wrong button.** It used a positional index (`app.button[1]`) that resolves to the database-refresh button once the Analyst panels render, so the control it claimed to test was never exercised. The test now clicks the control by label.
3. **The route simulator raised `KeyError: 'Order City'`.** The dashboard loads an explicit column set that does not include `Order City`, but the simulator required it. The feature was broken in the running app while the evidence screenshot still showed the panel, because the screenshot was captured before the button was pressed.
4. **`requirements.txt` allowed a Streamlit version the app cannot run on.** The dashboard calls `st.altair_chart(width="stretch")` and `st.dataframe(width="stretch")`, which need Streamlit 1.49 or newer. The declared floor was 1.39, where those calls raise `TypeError`. The floor is now 1.49.
5. **`build_documents.py` had no declared dependency.** It imports `python-docx`, which was absent from `requirements.txt`, so a clean install could not regenerate the deliverables.
6. **The FastAPI service leaked a SQLite connection per request.** A `sqlite3` connection's context manager commits the transaction but does not close the connection. The endpoints now close explicitly.
