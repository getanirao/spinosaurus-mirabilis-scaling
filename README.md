# Spinosaurus mirabilis — crest hydrodynamics & morphology

CFD screening and source-backed morphological analysis of the scimitar-crested
*Spinosaurus mirabilis*, using the Nobilis 2 artist mesh as a geometry surrogate.

## Repository structure

```
.
├── geometry/                          # 3D geometry pipeline
│   ├── source/                        #   original Nobilis 2 artist .blend
│   ├── derived/                       #   STLs, parametric hulls, wraps
│   └── scripts/                       #   hull generators and build tools
├── results/
│   ├── hydrodynamics/                 # Analytical crest-drag model
│   │   ├── crest_hydrodynamics.py     #   Monte Carlo sensitivity model
│   │   ├── build_crest_pressure_figure.py  # SVG figure renderer
│   │   ├── crest_hydrodynamics_inputs.csv
│   │   ├── crest_hydrodynamics_summary.csv
│   │   ├── crest_hydrodynamics_report.md
│   │   └── crest_pressure_comparison.svg
│   └── simscale/
│       ├── analyze_run.py             #   Compiles residual/force/moment stats
│       └── mirabilis_crest_present_U2mps/  # Completed crest-present CFD run
│           ├── raw/                   #   Exported solver telemetry
│           ├── figures/               #   Pressure and velocity cutting planes
│           ├── summary.csv            #   Compiled stability statistics
│           └── mesh_quality.txt       #   Mesh provenance and quality
├── data_ingestion.py                  # Bone measurement table ingestion
├── mirabilis_analysis.py              # Public evidence summary
├── mirabilis_habitat_analysis.py      # Habitat evidence comparison
├── mirabilis_integrated_analysis.py   # Combined morphology/habitat synthesis
├── mirabilis_evidence.csv
├── mirabilis_habitat_evidence.csv
├── mirabilis_density_context.csv
└── README.md
```

## Analysis tracks

### 1. Morphological & evidence analysis (Python)

Source-backed scripts that convert public claims about *S. mirabilis* and
*S. aegyptiacus* into a compact, reproducible quantitative summary.

| Script | What it does |
|--------|-------------|
| `mirabilis_analysis.py` | Summarizes public claims (body length, mass, crest height) with source attribution |
| `mirabilis_habitat_analysis.py` | Compares habitat evidence across species |
| `mirabilis_integrated_analysis.py` | Combines morphology, density context, and habitat into a synthesis |
| `data_ingestion.py` | Ingests bone measurement tables for regression-ready grids |

### 2. CFD hydrodynamics (SimScale + analytical model)

Two complementary approaches to estimate crest hydrodynamic loading:

**Analytical model** (`results/hydrodynamics/`): 100,000-draw Monte Carlo
sensitivity model treating the crest as a thickened sagittal blade. Current
median prediction: *S. mirabilis* head-first entry crest load = **20.1 N**
(4.4× the *S. aegyptiacus* fragment baseline).

**SimScale CFD** (`results/simscale/`): Completed crest-present steady RANS
run (k-omega SST, 1.6M cells, Uy = +2 m/s, 1,000 iterations). Key checkpoint:
- Final residuals: Ux = 1.6e-5, Uy = 9.3e-7, Uz = 1.6e-5, p = 1.9e-4
- Total Y-force over final 200 samples: **287.6 ± 0.18 N**
- Total moment X over final 200 samples: **-25.9 ± 0.46 N·m**

> A matched crest-reduced control run is needed before reporting a crest drag
> penalty. The current result is a numerical checkpoint, not a comparative
> biological result.

## Requirements

- Python 3
- `pandas`, `numpy`

## Run

```bash
# Morphology / evidence
python mirabilis_analysis.py
python mirabilis_habitat_analysis.py
python mirabilis_integrated_analysis.py

# Crest hydrodynamics analytical model
python results/hydrodynamics/crest_hydrodynamics.py \
  --output-csv results/hydrodynamics/crest_hydrodynamics_summary.csv \
  --output-markdown results/hydrodynamics/crest_hydrodynamics_report.md

# SVG comparison figure
python results/hydrodynamics/build_crest_pressure_figure.py

# Compile SimScale telemetry into summary statistics
python results/simscale/analyze_run.py results/simscale/mirabilis_crest_present_U2mps
```

## Third-party geometry attribution

> "Spinosaurus mirabilis" (https://skfb.ly/pKMVN) by Nobilis 2 is licensed
> under [Creative Commons Attribution 4.0]
> (http://creativecommons.org/licenses/by/4.0/).

The original `.blend` is preserved at `geometry/source/` as an immutable
source asset. All derived surfaces document their origin from this mesh and
are not represented as newly recovered anatomy.