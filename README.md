# Spinosaurus mirabilis scaling

This repository contains a small, source-backed analysis prototype for studying `Spinosaurus mirabilis` in context with `S. aegyptiacus`.

The current focus is not just raw size comparison. The repo is organized around two complementary questions:

1. What measurement and scaling signals distinguish `S. mirabilis` from better-documented spinosaurids?
2. What ecological context makes `S. mirabilis` meaningfully different from `S. aegyptiacus`?

## What the data says

The current habitat coding is based on 10 evidence rows from 5 public sources. The coded result is:

| Taxon | Inland-riparian | Coastal-inland margin | Coastal margin | Nearshore/marginal | Inland access | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `S. mirabilis` | 14.0 | 0.0 | 0.0 | 0.0 | 0.0 | Strongly inland-riparian |
| `S. aegyptiacus` | 0.0 | 5.0 | 2.0 | 3.0 | 2.0 | Mixed, coastal-leaning |

That is the reason the README now claims a habitat contrast:

- `S. mirabilis` is not just "water-adjacent"; it is coded as strongly inland-riparian.
- `S. aegyptiacus` has mixed evidence and still leans toward coastal / marginal-water context.
- The difference is large enough to support a working hypothesis that `S. mirabilis` may represent a more explicitly inland display ecology.

This is still a hypothesis, not a final conclusion. But now the hypothesis is anchored in a coded evidence table instead of only narrative prose.

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

## Evidence base

Primary public sources used in the current analysis:

- [UChicago News on `S. mirabilis`](https://news.uchicago.edu/story/hell-heron-dinosaur-discovered-central-sahara)
- [PubMed record for the `Science` paper](https://pubmed.ncbi.nlm.nih.gov/41712711/)
- [UChicago/BSD news coverage](https://biologicalsciences.uchicago.edu/news/new-scimitar-crested-spinosaurus-species-discovered-central-sahara)
- [eLife `S. aegyptiacus` reanalysis](https://elifesciences.org/articles/80092)
- [PLOS One paleoenvironments paper](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0147031)

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
