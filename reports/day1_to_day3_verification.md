# Day 1–3 Build Verification

**Verified on:** 23 October 2026

## Day 1 — Data foundation

- Raw dataset loaded: 180,519 rows
- Exact duplicate rows removed: 0
- Invalid actual/scheduled duration rows removed: 0
- Analytics-ready rows: 180,519
- Cleaned dataset, KPI summaries, data-quality profile, and EDA notebook produced
- Pipeline rerun successfully

## Day 2 — Dashboard core

- KPI overview: complete
- Delivery-classification and source-status charts: complete
- Delay-gap and source-risk charts: complete
- Shipping-mode comparison: complete
- Regional, market, and country diagnostics: complete
- Sidebar filters: complete

## Day 3 — Dashboard completion

- Geographic delay-risk map: complete
- Clear-all-filters control: complete
- Filtered CSV export: complete
- Decision-ready insights: complete
- README updated with architecture, scope, and run instructions: complete

## Automated checks passed

1. Python source compilation
2. Jupyter notebook JSON validity
3. Day 1 pipeline execution
4. Default Streamlit dashboard rendering
5. Shipping-mode filter state (`First Class` -> 27,814 shipments)
6. Clear-all-filters behavior (returns to 180,519 shipments)
7. Exact narrow filter case from testing (`First Class`, `Africa`, `North Africa`, `Argelia`, `Consumer` -> 30 shipments, 100% delayed)
8. Git whitespace validation

## Scope remaining after the 3-day build

- Research paper and executive summary
- Optional public deployment
- Screenshots and recorded demo for submission
- GitHub commit/push and final submission packaging
- Optional predictive delay model or route optimization (not part of the current diagnostic dashboard)
