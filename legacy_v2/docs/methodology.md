# EV-GRID INDIA v2 — Methodology

The product story is: **EV demand -> current charging supply -> spatial gap -> future demand -> required supply -> candidate priority zones.**

## Defensibility
- Keep source, retrieval date and transformation notes for every real dataset.
- Never present synthetic values as official data.
- Keep EV/charger planning target configurable.
- Validate forecasting chronologically to avoid future-data leakage.
- Explain recommendation factors in plain language.
- Treat district-zone ranking as planning intelligence, not construction approval.

## Sensitivity tests to add before final submission
1. Compare Random Forest with a naive last-year baseline.
2. Run several EV/charger target values.
3. Test multiple gap-score weight sets.
4. Measure how stable top-ranked zones remain across scenarios.
5. Report data coverage and missing fields.
