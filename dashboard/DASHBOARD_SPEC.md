# Medicine Price Gap — Power BI Dashboard Spec

A 4-page interactive Power BI dashboard on the cleaned Indian medicines dataset.

## Data model

Import `data/medicines_clean.csv` (~246k rows — Power BI handles it easily) as
`medicines`. Key columns: `price`, `price_per_unit`, `pack_type`, `full_composition`,
`salt_name`, `manufacturer_name`, `therapy_category`, `affordability_index`,
`premium_ratio`, `is_combination_drug`.

## DAX measures

```DAX
Medicines        = COUNTROWS(medicines)
Compositions     = DISTINCTCOUNT(medicines[full_composition])
Manufacturers    = DISTINCTCOUNT(medicines[manufacturer_name])
Median PPU       = MEDIAN(medicines[price_per_unit])
Pct Over 2x      = DIVIDE(CALCULATE(COUNTROWS(medicines), medicines[affordability_index] > 2), COUNTROWS(medicines))
Pct Over 5x      = DIVIDE(CALCULATE(COUNTROWS(medicines), medicines[affordability_index] > 5), COUNTROWS(medicines))
Avg Premium      = AVERAGE(medicines[premium_ratio])

-- Price ratio per composition+formulation (put comp_and_type on the axis):
Price Ratio      = DIVIDE(MAX(medicines[price_per_unit]), MIN(medicines[price_per_unit]))
Brand Count      = COUNTROWS(medicines)
```

For the "biggest gaps" and "competition paradox" visuals, build a summarized table
(Modeling → New table) grouping by `comp_and_type` with `Brand Count` and `Price Ratio`,
then filter to `Brand Count >= 30` (gaps) or bin `Brand Count` (paradox).

## Pages

### Page 1 — Overview
- **KPI cards:** Medicines, Compositions, Manufacturers, `Pct Over 2x`, `Median PPU`
- **Column:** Affordability-index histogram (bins of `affordability_index`, colored green→amber→red)
- **Bar:** Medicines by `pack_type`
- **Slicer:** `pack_type` (formulation) driving the page

### Page 2 — Price Gaps
- **Bar:** Top 15 `comp_and_type` by `Price Ratio` (≥30 brands) — the extreme gaps
- **Column:** Median `Price Ratio` by brand-count bin (the competition paradox: gap *grows* with competition)

### Page 3 — Manufacturers
- **Bar:** Top 12 manufacturers by `Avg Premium` (≥50 products) — most overpriced, red
- **Bar:** Bottom 12 by `Avg Premium` — most affordable (generics), green

### Page 4 — Categories & Molecules
- **Bar:** Median `Price Ratio` by `therapy_category`
- **Bar:** Per-unit saving (costliest − cheapest) for common household molecules
  (Paracetamol, Cetirizine, Metformin, …)

## Interaction
- `pack_type` and `therapy_category` slicers; all visuals cross-filter
- Reserve red for "overpriced / expensive", green for "affordable" — semantic, not decorative
