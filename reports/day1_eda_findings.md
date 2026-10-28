# Day 1 — Data Audit and Exploratory Findings

## Dataset readiness

| Check | Result |
|---|---:|
| Source rows | 180,519 |
| Exact duplicate rows removed | 0 |
| Rows with invalid shipping duration removed | 0 |
| Analytics-ready rows | 180,519 |

The source file is encoded as Windows-1252, so the pipeline reads UTF-8 first and then safely falls back to Windows-1252.

## Delivery-performance KPI baseline

| KPI | Value |
|---|---:|
| Total shipments | 180,519 |
| On-time or early delivery rate | 42.72% |
| Delayed delivery rate from calculated delay gap | 57.28% |
| Average delivery delay gap | 0.57 days |
| Source late-delivery-risk ratio | 54.83% |

`delivery_delay_gap = Days for shipping (real) - Days for shipment (scheduled)`.

- Negative gap: Early
- Zero gap: On Time
- Positive gap: Delayed

## Initial findings

1. **First Class needs investigation.** It has 27,814 shipments and a 100.00% calculated delayed-delivery rate, with an average delay gap of 1.00 day.
2. **Second Class is the next largest operational concern.** It has 35,216 shipments, a 79.73% delayed-delivery rate, and a 1.99-day average delay gap.
3. **Standard Class carries the most volume** (107,752 shipments) but has the best calculated on-time-or-early rate at 60.23%.
4. **Central Africa has the highest regional delayed-delivery rate** at 60.70%, but only 1,677 shipments. High-volume regions such as Western Europe (27,109 shipments) need priority alongside high-risk low-volume regions.
5. **Customer segments are similar.** Consumer, Corporate, and Home Office each have roughly a 57% calculated delayed-delivery rate, so segment alone is unlikely to explain the main issue.

## Dashboard metric rule

The calculated delayed-delivery rate (57.28%) does not exactly equal the source `Late_delivery_risk` ratio (54.83%). The dashboard must display them as **separate metrics**:

- **Calculated delay performance** uses actual versus scheduled shipping days.
- **Source late-delivery risk** uses the dataset's pre-existing risk flag.

Do not label one as the other or silently replace either metric. The mismatch itself is a valid data-quality/business-definition observation.

## Scope constraint

This dataset contains no order or delivery date field. The first dashboard version will not include a date-range filter. It will filter by shipping mode, order region, country, market, and customer segment instead.
