# Spinosaurus mirabilis scaling

This repository contains a small, source-backed analysis prototype for studying `Spinosaurus mirabilis` with a combined lens:

- quantitative morphology
- density context from the better-documented `S. aegyptiacus` literature
- qualitative ecological context

The goal is not to predict geology. It is to use measurements and contextual evidence together to make a species-level generalization about what makes `S. mirabilis` distinctive.

## Working idea

The current hypothesis is that `S. mirabilis` is best interpreted as:

- a crest-dominant spinosaur
- with an inland-riparian ecological setting
- whose novelty is strongest in display morphology and habitat differentiation
- rather than in any claim that density alone proves a new aquatic mode

## What is included

- `data_ingestion.py`  
  Loads a bone measurement table, identifies specimen IDs, separates independent proxies from dependent variables, and emits telemetry for regression-ready data.

- `mirabilis_analysis.py`  
  Summarizes public claims about `S. mirabilis` and the UChicago Fossil Lab into a compact quantitative report.

- `mirabilis_habitat_analysis.py`  
  Compares public habitat evidence for `S. mirabilis` and `S. aegyptiacus` to show the ecological contrast used in the synthesis.

- `mirabilis_integrated_analysis.py`  
  Combines crest/body-size data, density context, and habitat evidence into one integrated generalization.

- `mirabilis_evidence.csv`  
  Source-backed evidence rows used by the general analysis script.

- `mirabilis_habitat_evidence.csv`  
  Source-backed habitat evidence rows used by the ecological comparison script.

- `mirabilis_density_context.csv`  
  Density and compactness context from the `S. aegyptiacus` literature used to avoid overreading a single density proxy.

## Main finding so far

The integrated analysis currently points to a simple generalization:

- `S. mirabilis` has a tall crest relative to its estimated body length.
- Its habitat evidence is strongly inland-riparian.
- Density work on `S. aegyptiacus` shows why compactness alone should not be overinterpreted.
- Put together, the clearest signal is display specialization in a riverine setting, not a body-plan revolution.

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
python mirabilis_integrated_analysis.py
```

To write a markdown report:

```bash
python mirabilis_habitat_analysis.py --output-markdown report.md
python mirabilis_integrated_analysis.py --output-markdown report.md
```

## Notes

This is an early prototype. The current value is in framing a testable hypothesis and organizing public evidence into something reproducible.
