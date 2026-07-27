# Spinosaurus mirabilis scaling

This repository contains a small, source-backed analysis prototype for studying `Spinosaurus mirabilis` in context with `S. aegyptiacus`.

The current focus is not just raw size comparison. The repo is organized around two complementary questions:

1. What measurement and scaling signals distinguish `S. mirabilis` from better-documented spinosaurids?
2. What ecological context makes `S. mirabilis` meaningfully different from `S. aegyptiacus`?

## What is included

- `data_ingestion.py`  
  Loads a bone measurement table, identifies specimen IDs, separates independent proxies from dependent variables, and emits telemetry for regression-ready data.

- `mirabilis_analysis.py`  
  Summarizes public claims about `S. mirabilis` and the UChicago Fossil Lab into a compact quantitative report.

- `mirabilis_habitat_analysis.py`  
  Compares public habitat evidence for `S. mirabilis` and `S. aegyptiacus` to highlight the ecological contrast between inland-riparian and coastal-margin contexts.

- `mirabilis_evidence.csv`  
  Source-backed evidence rows used by the general analysis script.

- `mirabilis_habitat_evidence.csv`  
  Source-backed habitat evidence rows used by the ecological comparison script.

## Main finding so far

The strongest current differentiator is ecological:

- `S. mirabilis` is coded as strongly inland-riparian.
- `S. aegyptiacus` is more mixed and coastal-leaning.

That suggests a useful hypothesis: the tall crest in `S. mirabilis` may have been especially relevant in a visually open river corridor, where display and species recognition would travel farther.

## Requirements

- Python 3
- `pandas`
- `numpy`

## Run

```bash
python mirabilis_analysis.py
python mirabilis_habitat_analysis.py
```

To write a markdown report:

```bash
python mirabilis_habitat_analysis.py --output-markdown report.md
```

## Notes

This is an early prototype. The current value is in framing a testable hypothesis and organizing public evidence into something reproducible.
