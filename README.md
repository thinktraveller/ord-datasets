# ord-datasets

[中文](README-zh.md)

This is a provenance-preserving standardization and release workspace for the Open Reaction Database (ORD). It deliberately separates the near-complete reaction corpus from task-specific, model-ready tables so that a modeling subset is never mistaken for the complete corpus.

| Release | Intended use | Scope | Download |
|---|---|---|---|
| **Full corpus** `v0.2.0-corpus-preview-1` | Inspect complete ORD reaction JSON, re-extract fields, and trace individual rows | 41 packages; 53 pinned ORD sources; 2,428,291 reactions; 12.23 GiB | [Immutable Hugging Face tag](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1), commit `260cde0feb414c75b2bf971d6f3a4dbbee7b2e95` |
| **Model-ready** `v0.1.0-model-ready-preview-1` | Directly analyze yield, conversion, LC response, or ee | 19 targets from 15 packages; 128,712 included and 499 excluded decisions; 26.6 MiB across the `*-dataset.csv` files, 201.2 MiB total | [Browse individual datasets on `main`](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready); [immutable release](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1), commit `7d52dd27071c5625008a14737a1a8e1252ae6217` |

> **Two access paths, the same CSV content:** `datasets/model-ready/` on `main` keeps each main table byte-identical to the published model-ready snapshot, but gives it a semantic `*-dataset.csv` filename and separate English and Chinese target guides for convenient browsing. Cite the immutable release when its exact historical package layout matters. The much larger full-corpus payload remains on Hugging Face rather than `main`.

## Repository layout

```text
ord-datasets/
├── README.md                     # English guide
├── README-zh.md                  # Chinese guide
├── datasets/
│   ├── README.md                 # Dataset-area overview
│   ├── corpus/                   # Full-corpus catalog; payload is on Hugging Face
│   └── model-ready/              # 19 individual modelling targets
│       └── <target-slug>/
│           ├── README.md         # English target guide
│           ├── README-zh.md      # Chinese target guide
│           ├── <target-slug>-dataset.csv
│           ├── schema.json       # Columns and label definition
│           ├── row-map.csv       # Row-level ORD lineage
│           ├── audit.jsonl       # Label-selection decisions
│           ├── exclusions.csv    # Excluded records and reasons
│           ├── source-links.json # Pinned ORD source files
│           ├── metadata.json     # Scope, licence, and readiness state
│           ├── yonod-config.json
│           ├── target-build-provenance.json
│           └── checksums.csv
├── pipeline/                     # Build, validation, schemas, and tests
├── provenance/                   # Source, artifact, and row-lineage records
├── reports/                      # Data-quality, licence, and release evidence
└── project-docs/                 # Project plan and build record
```

## Getting started

### Which release should I download?

- Start with the smaller **model-ready release** if you want an ordinary table for analyzing conditions against yield, conversion, LC response, or ee. Each target's `<target-slug>-dataset.csv` opens as a conventional CSV.
- Download only the relevant package from the **full corpus release** if you need experimental setup, additions, workups, analytical details, or the complete nested ORD record. You do not need the entire 12.23 GiB corpus for one reaction family.
- A reaction may be reused by multiple model-ready targets. Consequently, target row counts must not be added and reported as a count of independent reactions; 2,428,291 is the corpus-wide reaction count for this release.

To download only one model-ready table in a browser:

1. Select its name in the [19-target inventory](#19-model-ready-targets).
2. Open the semantic `<target-slug>-dataset.csv` file in that directory.
3. Select **Download raw file** (the downward-arrow button at the upper right of the file view).
4. Also download `schema.json` and `metadata.json` if you need to interpret the columns, label, units, or readiness status. Keep the ten data/provenance files and the target's `README.md` or `README-zh.md` together when provenance and auditability matter.

To check out one complete target directory without checking out every dataset, copy the commands below and replace the final directory name with the target you want:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/thinktraveller/ord-datasets.git
cd ord-datasets
git sparse-checkout set datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent
```

To download all 19 model-ready targets or the full corpus, use:

```bash
# 19 model-ready targets
git clone --depth 1 https://github.com/thinktraveller/ord-datasets.git

# Full corpus (large; requires a Git environment with Hugging Face/Xet support)
git clone --depth 1 --branch v0.2.0-corpus-preview-1 https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus
```

### What is in each package?

Every full-corpus package contains five files:

| File | Purpose |
|---|---|
| `reactions.csv` | Main table. Each row is one reaction; `reaction_json` contains the complete ORD record. |
| `schema.json` | Defines the five-column contract of the main table. |
| `source-links.json` | Provides the original Parquet URL pinned to an exact ORD commit, source size, and SHA-256. |
| `metadata.json` | Records the dataset name, row count, members, and license. |
| `checksums.csv` | Detects a damaged or modified download. |

All 41 corpus packages use the same fields:

| Field | Meaning |
|---|---|
| `physical_dataset_id` | Identifier of the original physical ORD dataset. |
| `source_file` | Path of the original Parquet file in the ORD repository. |
| `reaction_id` | Unique identifier assigned to the reaction by ORD. |
| `row_index` | Position in the original physical dataset, **counted from zero**. |
| `reaction_json` | Complete nested reaction content, including inputs, reagents, catalysts, solvents, conditions, products, measurements, and provenance. |

Every model-ready target contains ten data/provenance files plus separate English and Chinese guides:

| File | Purpose |
|---|---|
| `<target-slug>-dataset.csv` | Analysis-ready table; every row is an included reaction. |
| `schema.json` | **Read this first:** exact columns, field roles, label definition, and extraction rule. |
| `row-map.csv` | Connects each main-table row to its ORD reaction. |
| `audit.jsonl` | One JSON object per label decision, including candidates, selected value, and reason. |
| `exclusions.csv` | Records not included in the main table and their reasons. An empty file still retains its header. |
| `source-links.json` | Revision-pinned original ORD files and hashes. |
| `metadata.json` | Label unit, included/excluded counts, readiness status, and other metadata. |
| `yonod-config.json` | Modeling field roles and configuration. |
| `target-build-provenance.json` | Inputs and transformations used to build the target. |
| `checksums.csv` | SHA-256 and size of the data/provenance files above (the explanatory README is not part of this checksum set). |
| `README.md` | English plain-language guide to this target's scope, label, fields, filtering, sources, status, and reaction tracing. |
| `README-zh.md` | Chinese version of the same target guide. |

Use `row-map.csv`, not row order or a molecule string, to recover source identity.

### Filtering rules

The corpus layer does not filter rows by yield or label. It groups 53 frozen physical sources into 41 semantic packages without changing reaction counts. Publication removes literal email values from `reaction_json` without removing rows. Original Parquet payloads, `_needs_review`, credentials, and clean-room duplicates are outside the published payload.

The model-ready layer processes only each target's declared physical subset. Most targets require one structured scalar measurement and perform no aggregation; flow targets use their declared multi-target rule, and signed ee is defined as `S-R`. Every rejected decision is retained in `exclusions.csv` and `audit.jsonl`. The actual reason codes and readiness state for every target are listed below.

### Trace one reaction step by step (verified example)

This example starts with the first data row of the Ahneman C-N model-ready target on `main`.

1. Open [`ahneman-c-n-cross-coupling-yield-percent-dataset.csv`](https://github.com/thinktraveller/ord-datasets/blob/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/ahneman-c-n-cross-coupling-yield-percent-dataset.csv). The header is line 1, so the first data record has `csv_row_number = 2`; its `yield_percent` is `54.390403747558594`.
2. In [`row-map.csv`](https://github.com/thinktraveller/ord-datasets/blob/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/row-map.csv), find `csv_row_number = 2`. It resolves to physical dataset `ord_dataset-46ff9a32d9e04016b9380b1b1ef949c3`, zero-based source row `3239`, reaction `ord-001c0b7f789d41b48e325967a9941ad6`, and label-decision hash `d966e2c9e5acdd4ad6becd3c73ba17cc92c9c205913e86cff10c430a5395868f`.
3. Search [`audit.jsonl`](https://github.com/thinktraveller/ord-datasets/blob/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/audit.jsonl) for that label-decision hash. The record says the row was included because there was one unique candidate: a UPLC `YIELD` percentage with value `54.390403747558594`. This proves how the label was selected.
4. Match the physical dataset ID in [`source-links.json`](https://github.com/thinktraveller/ord-datasets/blob/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/source-links.json). It gives ORD revision `83f971f586f6ad18f358ae4ae99d045e94ed2066`, the immutable Parquet URL, and source SHA-256 `39440ea3e5442dddbb4daccbc48fb53940724085327c0e3b82909e1fd8cc661a`.
5. In the corpus package's [`reactions.csv`](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/ahneman-c-n-cross-coupling/reactions.csv), match the physical dataset ID plus `row_index = 3239`. The recovered `reaction_id` is the same value found in step 2, and `reaction_json` is the full ORD record.
6. Optionally download the source Parquet through `source_file_url` and compare its SHA-256. A match proves byte identity with the frozen input used by this release.

Avoid opening a large `reactions.csv` in Excel: `reaction_json` can be a very long cell and may be truncated. If both directories above are downloaded, the following dependency-free Python 3 example performs the lookup safely, including CSV fields that contain embedded newlines. Change only the first two paths.

```python
import csv
import json
from pathlib import Path

target_dir = Path("replace/with/path/to/ahneman-c-n-cross-coupling-yield-percent")
corpus_csv = Path("replace/with/path/to/ahneman-c-n-cross-coupling/reactions.csv")
wanted_csv_row = "2"

with (target_dir / "ahneman-c-n-cross-coupling-yield-percent-dataset.csv").open(encoding="utf-8", newline="") as f:
    dataset_row = next(row for number, row in enumerate(csv.DictReader(f), start=2)
                       if str(number) == wanted_csv_row)

with (target_dir / "row-map.csv").open(encoding="utf-8", newline="") as f:
    row_map = next(row for row in csv.DictReader(f)
                   if row["csv_row_number"] == wanted_csv_row)

with (target_dir / "audit.jsonl").open(encoding="utf-8") as f:
    audit = next(item for item in map(json.loads, f)
                 if item["label_decision_id"] == row_map["label_decision_id"])

source_links = json.loads((target_dir / "source-links.json").read_text(encoding="utf-8"))
source = next(item for item in source_links["links"]
              if item["physical_dataset_id"] == row_map["physical_dataset_id"])

with corpus_csv.open(encoding="utf-8", newline="") as f:
    corpus_row = next(row for row in csv.DictReader(f)
                      if row["physical_dataset_id"] == row_map["physical_dataset_id"]
                      and row["row_index"] == row_map["source_row_index"])

print("model row:", dataset_row)
print("row map:", row_map)
print("label audit:", audit)
print("pinned source:", source)
print("ORD reaction_id:", corpus_row["reaction_id"])
print(json.dumps(json.loads(corpus_row["reaction_json"]), ensure_ascii=False, indent=2))
```

## Complete dataset inventory

The numbers below come from accepted release candidates verified byte-for-byte against the remote releases. `MiB`/`GiB` are binary units. “Data file / package” means the main CSV versus every published file in that dataset directory.

### 41 full-corpus packages

All packages share the five corpus fields and the same filtering rule: no label-based row removal, only literal-email redaction. Select a dataset name to browse its files, or “pinned ORD source” for pinned Parquet URLs, source sizes, counts, licenses, and hashes.

| Dataset | Reactions | ORD sources | `reactions.csv` / package | Publication and pinned source |
|---|---:|---:|---:|---|
| [Ahneman C-N Cross-Coupling](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/ahneman-c-n-cross-coupling) | 4,312 | 1 | 30.6 MiB / 30.6 MiB | [10.1126/science.aar5169](https://doi.org/10.1126/science.aar5169)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/ahneman-c-n-cross-coupling/source-links.json) |
| [AIChemEco Amide-Coupling Conditions](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/aichemeeco-amide-coupling-conditions) | 47,015 | 1 | 474.3 MiB / 474.3 MiB | [10.1039/d5sc03364k](https://doi.org/10.1039/d5sc03364k)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/aichemeeco-amide-coupling-conditions/source-links.json) |
| [AstraZeneca ELN Buchwald-Hartwig Yields](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/astrazeneca-eln-buchwald-hartwig-yields) | 750 | 1 | 2.7 MiB / 2.7 MiB | [10.26434/chemrxiv.14589498.v2](https://doi.org/10.26434/chemrxiv.14589498.v2)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/astrazeneca-eln-buchwald-hartwig-yields/source-links.json) |
| [Asymmetric Alkylation Chemical Space](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/asymmetric-alkylation-chemical-space) | 1,430 | 1 | 15.6 MiB / 15.6 MiB | [10.1038/s41467-023-42446-5](https://doi.org/10.1038/s41467-023-42446-5)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/asymmetric-alkylation-chemical-space/source-links.json) |
| [Automated Kinetic Profiling HPLC Optimization](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/automated-kinetic-profiling-hplc-optimization) | 7 | 1 | 923.1 KiB / 926.5 KiB | [10.1039/c9re00086k](https://doi.org/10.1039/c9re00086k)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/automated-kinetic-profiling-hplc-optimization/source-links.json) |
| [Aza-Heck Impatien A Ligand Screen](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/aza-heck-impatien-a-ligand-screen) | 24 | 1 | 297.6 KiB / 300.9 KiB | [pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/aza-heck-impatien-a-ligand-screen/source-links.json) |
| [Cernak Miniaturized Diversity Reactions](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/cernak-miniaturized-diversity-reactions) | 2,696 | 3 | 26.2 MiB / 26.2 MiB | [10.1038/s44160-023-00351-1](https://doi.org/10.1038/s44160-023-00351-1)<br>[pinned ORD source ×3](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/cernak-miniaturized-diversity-reactions/source-links.json) |
| [Cernak Ultra-HTE C-N Coupling](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/cernak-ultra-hte-c-n-coupling) | 50,688 | 1 | 485.5 MiB / 485.5 MiB | [10.1021/jacs.6c05959](https://doi.org/10.1021/jacs.6c05959)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/cernak-ultra-hte-c-n-coupling/source-links.json) |
| [Chan-Lam Sulfonamide-Boronic-Acid Coupling](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/chan-lam-sulfonamide-boronic-acid-coupling) | 9,632 | 1 | 87.6 MiB / 87.6 MiB | [10.26434/chemrxiv-2024-22jrq](https://doi.org/10.26434/chemrxiv-2024-22jrq)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/chan-lam-sulfonamide-boronic-acid-coupling/source-links.json) |
| [Chemistry Informer Libraries](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/chemistry-informer-libraries) | 354 | 2 | 1.5 MiB / 1.5 MiB | [10.1039/C5SC04751J](https://doi.org/10.1039/C5SC04751J)<br>[pinned ORD source ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/chemistry-informer-libraries/source-links.json) |
| [ChemRxiv Decarboxylative Olefination Campaigns](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/chemrxiv-decarboxylative-olefination-campaigns) | 256 | 2 | 1.0 MiB / 1.0 MiB | [10.26434/chemrxiv.15001213/v1](https://doi.org/10.26434/chemrxiv.15001213/v1)<br>[pinned ORD source ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/chemrxiv-decarboxylative-olefination-campaigns/source-links.json) |
| [ChemRxiv Imidazole Arylation and Aniline Amidation](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/chemrxiv-imidazole-arylation-and-aniline-amidation) | 2,496 | 2 | 14.3 MiB / 14.3 MiB | [10.1038/s41586-024-07021-y](https://doi.org/10.1038/s41586-024-07021-y)<br>[pinned ORD source ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/chemrxiv-imidazole-arylation-and-aniline-amidation/source-links.json) |
| [Copper Enantioselective Alkene Hydroamination](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/copper-enantioselective-alkene-hydroamination) | 3 | 1 | 28.5 KiB / 32.0 KiB | [10.15227/orgsyn.095.0080](https://doi.org/10.15227/orgsyn.095.0080)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/copper-enantioselective-alkene-hydroamination/source-links.json) |
| [Deoxyfluorination Screen](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/deoxyfluorination-screen) | 80 | 1 | 320.6 KiB / 323.8 KiB | [10.1021/jacs.8b01523](https://doi.org/10.1021/jacs.8b01523)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/deoxyfluorination-screen/source-links.json) |
| [Electroreductive Alkenyl-Benzyl-Halide Coupling](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/electroreductive-alkenyl-benzyl-halide-coupling) | 27 | 1 | 196.4 KiB / 199.8 KiB | [10.1021/acscatal.9b01785](https://doi.org/10.1021/acscatal.9b01785)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/electroreductive-alkenyl-benzyl-halide-coupling/source-links.json) |
| [Flow Catechol Rearrangement](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/flow-catechol-rearrangement) | 1,227 | 1 | 14.7 MiB / 14.7 MiB | [10.48550/arXiv.2506.07619](https://doi.org/10.48550/arXiv.2506.07619)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/flow-catechol-rearrangement/source-links.json) |
| [Golden Pyridine-Nucleophile Cross-Coupling](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/golden-pyridine-nucleophile-cross-coupling) | 288 | 1 | 1.6 MiB / 1.6 MiB | [10.1016/j.chempr.2024.04.001](https://doi.org/10.1016/j.chempr.2024.04.001)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/golden-pyridine-nucleophile-cross-coupling/source-links.json) |
| [HTE Suzuki Coupling](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/hte-suzuki-coupling) | 376 | 1 | 1.3 MiB / 1.3 MiB | [10.1021/jacs.2c08592](https://doi.org/10.1021/jacs.2c08592)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/hte-suzuki-coupling/source-links.json) |
| [Imidazopyridine Three-Component Synthesis](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/imidazopyridine-three-component-synthesis) | 384 | 1 | 1.3 MiB / 1.3 MiB | [pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/imidazopyridine-three-component-synthesis/source-links.json) |
| [Islatravir Biocatalytic Cascade](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/islatravir-biocatalytic-cascade) | 3 | 1 | 27.3 KiB / 30.7 KiB | [10.1126/science.aay8484](https://doi.org/10.1126/science.aay8484)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/islatravir-biocatalytic-cascade/source-links.json) |
| [Microwave Biginelli Condensation](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/microwave-biginelli-condensation) | 48 | 1 | 192.9 KiB / 196.3 KiB | [10.1021/cc010044j](https://doi.org/10.1021/cc010044j)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/microwave-biginelli-condensation/source-links.json) |
| [Nano C-N Photochemistry Informer](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/nano-c-n-photochemistry-informer) | 1,728 | 1 | 16.7 MiB / 16.7 MiB | [10.1021/acs.accounts.0c00760](https://doi.org/10.1021/acs.accounts.0c00760)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/nano-c-n-photochemistry-informer/source-links.json) |
| [Newman 1-Octene Mizoroki-Heck](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/newman-1-octene-mizoroki-heck) | 96 | 1 | 1.2 MiB / 1.2 MiB | [pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/newman-1-octene-mizoroki-heck/source-links.json) |
| [Newman N-Vinylpyrrolidone Mizoroki-Heck](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/newman-n-vinyl-pyrrolidone-mizoroki-heck) | 96 | 1 | 906.4 KiB / 909.8 KiB | [pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/newman-n-vinyl-pyrrolidone-mizoroki-heck/source-links.json) |
| [Newman Styrene Mizoroki-Heck](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/newman-styrene-mizoroki-heck) | 96 | 1 | 812.6 KiB / 815.9 KiB | [pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/newman-styrene-mizoroki-heck/source-links.json) |
| [Newman Vinyl-Ether Mizoroki-Heck](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/newman-vinyl-ether-mizoroki-heck) | 96 | 1 | 1.0 MiB / 1.0 MiB | [pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/newman-vinyl-ether-mizoroki-heck/source-links.json) |
| [Nickel Suzuki-Miyaura Cross-Coupling](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/nickel-suzuki-miyaura-cross-coupling) | 450 | 1 | 2.6 MiB / 2.6 MiB | [10.1126/science.abj4213](https://doi.org/10.1126/science.abj4213)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/nickel-suzuki-miyaura-cross-coupling/source-links.json) |
| [NiCOlit Nickel Cross-Couplings](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/nicolit-nickel-cross-couplings) | 1,762 | 1 | 3.3 MiB / 3.3 MiB | [10.1002/chem.201603436](https://doi.org/10.1002/chem.201603436)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/nicolit-nickel-cross-couplings/source-links.json) |
| [Pfizer HTE Reaction Conditions](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/pfizer-hte-reaction-conditions) | 39,347 | 1 | 214.7 MiB / 214.7 MiB | [10.1038/s41557-023-01393-w](https://doi.org/10.1038/s41557-023-01393-w)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/pfizer-hte-reaction-conditions/source-links.json) |
| [Photocatalytic Aryl-Bromide Dehalogenation](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/photocatalytic-aryl-bromide-dehalogenation) | 1,152 | 1 | 6.3 MiB / 6.3 MiB | [10.1021/acscatal.0c02247](https://doi.org/10.1021/acscatal.0c02247)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/photocatalytic-aryl-bromide-dehalogenation/source-links.json) |
| [PyParser Oxazole C-H Activation](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/pyparser-oxazole-c-h-activation) | 48 | 1 | 411.1 KiB / 414.4 KiB | [pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/pyparser-oxazole-c-h-activation/source-links.json) |
| [Reizman Suzuki-Miyaura Feedback Optimization](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/reizman-suzuki-miyaura-feedback-optimization) | 385 | 4 | 2.1 MiB / 2.1 MiB | [10.1039/C6RE00153J](https://doi.org/10.1039/C6RE00153J)<br>[pinned ORD source ×4](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/reizman-suzuki-miyaura-feedback-optimization/source-links.json) |
| [Rexgen Direct Reaction SMILES](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/rexgen-direct-reaction-smiles) | 479,035 | 3 | 1.37 GiB / 1.37 GiB | [pinned ORD source ×3](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/rexgen-direct-reaction-smiles/source-links.json) |
| [Roche Borylation SURF](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/roche-borylation-surf) | 1,111 | 1 | 4.1 MiB / 4.1 MiB | [10.26434/chemrxiv-2023-nfq7h](https://doi.org/10.26434/chemrxiv-2023-nfq7h)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/roche-borylation-surf/source-links.json) |
| [Roche Minisci SURF](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/roche-minisci-surf) | 130 | 1 | 468.1 KiB / 471.3 KiB | [10.26434/chemrxiv-2023-nfq7h](https://doi.org/10.26434/chemrxiv-2023-nfq7h)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/roche-minisci-surf/source-links.json) |
| [Science HTE Palladium Cross-Coupling](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/science-hte-palladium-cross-coupling) | 1,824 | 2 | 16.4 MiB / 16.4 MiB | [10.1126/science.1259203](https://doi.org/10.1126/science.1259203)<br>[pinned ORD source ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/science-hte-palladium-cross-coupling/source-links.json) |
| [Shields Bayesian Arylation Optimization](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/shields-bayesian-arylation) | 1,984 | 2 | 12.4 MiB / 12.4 MiB | [10.1038/s41586-021-03213-y](https://doi.org/10.1038/s41586-021-03213-y)<br>[pinned ORD source ×2](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/shields-bayesian-arylation/source-links.json) |
| [sp3-Carboxyl Aryl-Halide Coupling](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/sp3-carboxyl-aryl-halide-coupling) | 24 | 1 | 181.0 KiB / 184.3 KiB | [pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/sp3-carboxyl-aryl-halide-coupling/source-links.json) |
| [Sulfonamide Flow-Synthesis Library](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/sulfonamide-flow-synthesis-library) | 39 | 1 | 193.6 KiB / 196.9 KiB | [10.1021/co400012m](https://doi.org/10.1021/co400012m)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/sulfonamide-flow-synthesis-library/source-links.json) |
| [Suzuki-Miyaura Nanoscale Screen](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/suzuki-miyaura-nanoscale-screen) | 5,760 | 1 | 29.8 MiB / 29.8 MiB | [10.1126/science.aap9112](https://doi.org/10.1126/science.aap9112)<br>[pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/suzuki-miyaura-nanoscale-screen/source-links.json) |
| [USPTO Granted-Patent Reactions](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/tree/v0.2.0-corpus-preview-1/datasets/corpus/uspto-grants-reactions) | 1,771,032 | 1 | 9.41 GiB / 9.41 GiB | [pinned ORD source ×1](https://huggingface.co/datasets/thinktraveller/ord-processed-reaction-corpus/blob/v0.2.0-corpus-preview-1/datasets/corpus/uspto-grants-reactions/source-links.json) |

### 19 model-ready targets

“Included / excluded” counts label decisions, and “filter” lists only observed exclusion reasons. Every target first limits input to its declared physical sources, then applies its `schema.json` label rule. Status letters describe **modeling/benchmark readiness**, not download availability; all 19 payloads are published and release-validated.

| Code | Repository status | Meaning |
|---|---|---|
| A | `active_generated_pending_release_validation` | Active target; downstream readiness gates were pending at build time. The payload has since passed release validation. |
| B | `generated_pending_campaign_evaluation` | Generated; campaign or grouping evaluation is still required before benchmark use. |
| C | `partial_scope_generated` | Covers only the declared physical subset, not the full logical dataset. |
| D | `research_only_benchmark_blocked` | Research-only; reliable run grouping is missing, blocking batch-benchmark claims. |
| E | `generated_with_source_caveat` | Source-measurement caveat; NiCOlit does not distinguish GC from isolated yield. |
| F | `generated_adapter_blocked` | Artifact exists, but its declared adapter/readiness gate remains blocked. |

| Target | Publication and source | Included / excluded | `*-dataset.csv` / package | Label | Observed exclusion | Status |
|---|---|---:|---:|---|---|:---:|
| [Ahneman C-N Cross-Coupling Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent) | [10.1126/science.aar5169](https://doi.org/10.1126/science.aar5169)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/ahneman-c-n-cross-coupling-yield-percent/source-links.json) | 4,312 / 0 | 1.2 MiB / 5.8 MiB | `yield_percent`<br>percent yield as defined by the source measurement | none | A |
| [Asymmetric Alkylation ee (S-R, %)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/asymmetric-alkylation-ee-s-minus-r-percent) | [10.1038/s41467-023-42446-5](https://doi.org/10.1038/s41467-023-42446-5)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/asymmetric-alkylation-ee-s-minus-r-percent/source-links.json) | 1,430 / 0 | 296.3 KiB / 4.3 MiB | `ee_s_minus_r_percent`<br>percentage points, S minus R | none | F |
| [Cernak Reductive-Amination Conversion (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/cernak-reductive-amination-conversion-percent) | [10.1038/s44160-023-00351-1](https://doi.org/10.1038/s44160-023-00351-1)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/cernak-reductive-amination-conversion-percent/source-links.json) | 1,152 / 0 | 323.4 KiB / 1.5 MiB | `conversion_percent`<br>percent conversion | none | B |
| [Cernak Suzuki-Coupling Conversion (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/cernak-suzuki-coupling-conversion-percent) | [10.1038/s44160-023-00351-1](https://doi.org/10.1038/s44160-023-00351-1)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/cernak-suzuki-coupling-conversion-percent/source-links.json) | 1,320 / 120 | 306.8 KiB / 1.8 MiB | `conversion_percent`<br>percent conversion | non-finite label | B |
| [Cernak Ultra-HTE C-N Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/cernak-ultra-hte-c-n-yield-percent) | [10.1021/jacs.6c05959](https://doi.org/10.1021/jacs.6c05959)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/cernak-ultra-hte-c-n-yield-percent/source-links.json) | 50,668 / 20 | 11.6 MiB / 68.2 MiB | `yield_percent`<br>percent yield as defined by the source measurement | label out of range | B |
| [Chan-Lam Sulfonamide-Coupling Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/chan-lam-sulfonamide-coupling-yield-percent) | [10.26434/chemrxiv-2024-22jrq](https://doi.org/10.26434/chemrxiv-2024-22jrq)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/chan-lam-sulfonamide-coupling-yield-percent/source-links.json) | 9,602 / 30 | 1.8 MiB / 12.8 MiB | `yield_percent`<br>percent yield as defined by the source measurement | label out of range | B |
| [ChemRxiv Aniline-Amidation Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/chemrxiv-aniline-amidation-yield-percent) | [10.1038/s41586-024-07021-y](https://doi.org/10.1038/s41586-024-07021-y)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/chemrxiv-aniline-amidation-yield-percent/source-links.json) | 957 / 3 | 232.7 KiB / 1.3 MiB | `yield_percent`<br>percent yield as defined by the source measurement | label out of range | A |
| [ChemRxiv Imidazole C-H Arylation Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/chemrxiv-imidazole-c-h-arylation-yield-percent) | [10.1038/s41586-024-07021-y](https://doi.org/10.1038/s41586-024-07021-y)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/chemrxiv-imidazole-c-h-arylation-yield-percent/source-links.json) | 1,529 / 7 | 384.8 KiB / 2.1 MiB | `yield_percent`<br>percent yield as defined by the source measurement | label out of range | A |
| [Flow Catechol Product 2 HPLC Response (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/flow-catechol-product-2-response-percent) | [10.48550/arXiv.2506.07619](https://doi.org/10.48550/arXiv.2506.07619)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/flow-catechol-product-2-response-percent/source-links.json) | 1,227 / 0 | 213.6 KiB / 2.9 MiB | `product_2_yield_percent`<br>HPLC percentage response; not isolated yield | none | D |
| [Flow Catechol Product 3 HPLC Response (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/flow-catechol-product-3-response-percent) | [10.48550/arXiv.2506.07619](https://doi.org/10.48550/arXiv.2506.07619)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/flow-catechol-product-3-response-percent/source-links.json) | 1,227 / 0 | 213.6 KiB / 2.9 MiB | `product_3_yield_percent`<br>HPLC percentage response; not isolated yield | none | D |
| [Flow Catechol Total-Product HPLC Response (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/flow-catechol-total-product-response-percent) | [10.48550/arXiv.2506.07619](https://doi.org/10.48550/arXiv.2506.07619)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/flow-catechol-total-product-response-percent/source-links.json) | 1,227 / 0 | 214.3 KiB / 3.7 MiB | `total_product_yield_percent`<br>HPLC percentage response; not isolated yield | none | D |
| [Nano C-N Photochemistry Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/nano-c-n-photochemistry-yield-percent) | [10.1021/acs.accounts.0c00760](https://doi.org/10.1021/acs.accounts.0c00760)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/nano-c-n-photochemistry-yield-percent/source-links.json) | 1,728 / 0 | 361.4 KiB / 2.3 MiB | `yield_percent`<br>percent yield as defined by the source measurement | none | A |
| [NiCOlit Nickel-Coupling Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/nicolit-nickel-coupling-yield-percent) | [10.1002/chem.201603436](https://doi.org/10.1002/chem.201603436)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/nicolit-nickel-coupling-yield-percent/source-links.json) | 1,669 / 93 | 157.0 KiB / 4.2 MiB | `yield_percent`<br>percent yield as defined by the source measurement | missing desired product<br>missing required reactant SMILES | E |
| [Pfizer HTE LC Area (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/pfizer-hte-lc-area-percent) | [10.1038/s41557-023-01393-w](https://doi.org/10.1038/s41557-023-01393-w)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/pfizer-hte-lc-area-percent/source-links.json) | 39,347 / 0 | 6.7 MiB / 65.9 MiB | `lc_area_percent`<br>LC/UV area percent; not isolated yield or conversion | none | B |
| [Photocatalytic Aryl-Bromide Dehalogenation Conversion (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/photocatalytic-aryl-bromide-dehalogenation-conversion-percent) | [10.1021/acscatal.0c02247](https://doi.org/10.1021/acscatal.0c02247)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/photocatalytic-aryl-bromide-dehalogenation-conversion-percent/source-links.json) | 1,152 / 0 | 232.7 KiB / 1.4 MiB | `conversion_percent`<br>percent conversion | none | A |
| [Roche Borylation Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/roche-borylation-yield-percent) | [10.26434/chemrxiv-2023-nfq7h](https://doi.org/10.26434/chemrxiv-2023-nfq7h)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/roche-borylation-yield-percent/source-links.json) | 890 / 221 | 193.5 KiB / 1.4 MiB | `yield_percent`<br>percent yield as defined by the source measurement | label out of range<br>missing desired product | B |
| [Science HTE Relative LC Area Ratio](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/science-hte-relative-lc-area-ratio) | [10.1126/science.1259203](https://doi.org/10.1126/science.1259203)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/science-hte-relative-lc-area-ratio/source-links.json) | 1,531 / 5 | 332.7 KiB / 8.0 MiB | `relative_product_lc_area_ratio`<br>dimensionless ratio (product LC area / internal-standard LC area) | invalid biphenyl internal-standard area | C |
| [Shields Arylation Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/shields-arylation-yield-percent) | [10.1038/s41586-021-03213-y](https://doi.org/10.1038/s41586-021-03213-y)<br>[pinned ORD source ×2](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/shields-arylation-yield-percent/source-links.json) | 1,984 / 0 | 370.5 KiB / 2.7 MiB | `yield_percent`<br>percent yield as defined by the source measurement | none | A |
| [Suzuki-Miyaura Nanoscale Yield (%)](https://github.com/thinktraveller/ord-datasets/tree/main/datasets/model-ready/suzuki-miyaura-nanoscale-yield-percent) | [10.1126/science.aap9112](https://doi.org/10.1126/science.aap9112)<br>[pinned ORD source ×1](https://github.com/thinktraveller/ord-datasets/blob/v0.1.0-model-ready-preview-1/datasets/model-ready/suzuki-miyaura-nanoscale-yield-percent/source-links.json) | 5,760 / 0 | 1.6 MiB / 8.1 MiB | `yield_percent`<br>percent yield as defined by the source measurement | none | A |

#### Per-target extraction and filtering rules

The table maps all 19 targets to their actual adapter and label policy. The adapter says where and under which chemical semantics a value is found; the policy says what to do with candidate measurements. R1–R8 are reading aids in this README, not data fields.

| Rule | `target_adapter` | `label_policy` | Targets | Plain-language rule |
|---|---|---|---|---|
| R1 | `generic` | `unique_structured_scalar_no_aggregation` | `ahneman-c-n-cross-coupling-yield-percent`<br>`chemrxiv-aniline-amidation-yield-percent`<br>`chemrxiv-imidazole-c-h-arylation-yield-percent`<br>`nano-c-n-photochemistry-yield-percent`<br>`photocatalytic-aryl-bromide-dehalogenation-conversion-percent`<br>`shields-arylation-yield-percent`<br>`suzuki-miyaura-nanoscale-yield-percent` | Select one structured scalar of the requested measurement type; never average multiple measurements. |
| R2 | `cernak_conversion` | `unique_structured_scalar_no_aggregation` | `cernak-reductive-amination-conversion-percent`<br>`cernak-suzuki-coupling-conversion-percent` | Extract one conversion value using the Cernak record structure; the Suzuki target rejects 120 non-finite values. |
| R3 | `unique_desired_product` | `unique_structured_scalar_no_aggregation` | `cernak-ultra-hte-c-n-yield-percent`<br>`chan-lam-sulfonamide-coupling-yield-percent`<br>`roche-borylation-yield-percent` | First require one identifiable desired product, then one structured yield for it; missing product or out-of-range values are rejected. |
| R4 | `science_hte_relative_lc_area_ratio` | `unique_structured_scalar_no_aggregation` | `science-hte-relative-lc-area-ratio` | Label is product LC area divided by biphenyl internal-standard area, not yield; invalid standard area is rejected. |
| R5 | `catechol_multitarget_v1` | `catechol_multitarget_v1:smiles_custom_name_hplc_yield` | `flow-catechol-product-2-response-percent`<br>`flow-catechol-product-3-response-percent`<br>`flow-catechol-total-product-response-percent` | Resolve Product 2/3 HPLC responses by SMILES/custom name; total response is their deterministic sum, with no cross-record aggregation. |
| R6 | `nicolit_reported_yield_float_percent` | `unique_structured_scalar_no_aggregation` | `nicolit-nickel-coupling-yield-percent` | Parse the reported NiCOlit floating-point percentage and require reactant SMILES/product; GC and isolated-yield conventions are not distinguished. |
| R7 | `signed_selectivity` | `signed_selectivity_v1:s_config_imms_percentage` | `asymmetric-alkylation-ee-s-minus-r-percent` | Convert the S-configured IMMS percentage to signed `S-R` ee; product stereochemistry determines the label but is not a feature. |
| R8 | `pfizer_lcms` | `unique_structured_scalar_no_aggregation` | `pfizer-hte-lc-area-percent` | Select one LC/UV area percentage; it is neither isolated yield nor conversion. |

#### Exact `*-dataset.csv` columns for every target

No column is omitted below. Columns are grouped only for readability into structure/composition/auxiliary fields, condition fields, and label; each package's `schema.json` is authoritative for exact roles. `—` means none.

Quick field guide:

- `reactant-*`, `reagent-*`, `catalyst-*`, `solvent-*`, and `product` usually contain standardized SMILES, a text representation of molecular structure. Numeric suffixes distinguish slots, not chemical importance.
- The suffixes in `temperature_c`, `reaction_time_s`, `residence_time_min`, `pressure_kpa`, and `illumination_wavelength_nm` mean degrees Celsius, seconds, minutes, kilopascals, and nanometres; `solvent_b_fraction` is the fraction of solvent B.
- `_raw` preserves a source value; `_gt_100` is a Boolean quality flag, not another yield.
- Yield, conversion, LC area, HPLC response, LC-area ratio, and signed ee are analytically distinct labels and must not be treated as interchangeable.

| Target slug | Structure, composition, and auxiliary fields | Conditions | Label |
|---|---|---|---|
| `ahneman-c-n-cross-coupling-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `catalyst-1`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `asymmetric-alkylation-ee-s-minus-r-percent` | `reactant-1`, `reactant-2`, `reactant-3`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5` | — | `ee_s_minus_r_percent` |
| `cernak-reductive-amination-conversion-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `reagent-3`, `catalyst-1`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `solvent-6`, `solvent-7` | `temperature_c`, `reaction_time_s` | `conversion_percent` |
| `cernak-suzuki-coupling-conversion-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `reagent-3`, `catalyst-1`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `solvent-6`, `solvent-7` | `reaction_time_s`, `reflux_value`, `conditions_are_dynamic_value` | `conversion_percent` |
| `cernak-ultra-hte-c-n-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `solvent-6`, `solvent-7`, `solvent-8`, `solvent-9`, `solvent-10`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `chan-lam-sulfonamide-coupling-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `solvent-1`, `solvent-2`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `chemrxiv-aniline-amidation-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `product` | `temperature_c`, `reaction_time_s`, `reflux_value`, `conditions_are_dynamic_value` | `yield_percent` |
| `chemrxiv-imidazole-c-h-arylation-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `reagent-2`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `product` | `temperature_c`, `reaction_time_s`, `reflux_value`, `conditions_are_dynamic_value` | `yield_percent` |
| `flow-catechol-product-2-response-percent` | `reactant_smiles`, `solvent_a_smiles`, `solvent_b_smiles`, `starting_material_recovery_percent_raw`, `product_sum_yield_percent_raw`, `mass_balance_sum_percent`, `starting_material_gt_100`, `mass_balance_gt_100`, `pressure_kpa_raw` | `solvent_b_fraction`, `temperature_c`, `residence_time_s`, `residence_time_min` | `product_2_yield_percent` |
| `flow-catechol-product-3-response-percent` | `reactant_smiles`, `solvent_a_smiles`, `solvent_b_smiles`, `starting_material_recovery_percent_raw`, `product_sum_yield_percent_raw`, `mass_balance_sum_percent`, `starting_material_gt_100`, `mass_balance_gt_100`, `pressure_kpa_raw` | `solvent_b_fraction`, `temperature_c`, `residence_time_s`, `residence_time_min` | `product_3_yield_percent` |
| `flow-catechol-total-product-response-percent` | `reactant_smiles`, `solvent_a_smiles`, `solvent_b_smiles`, `starting_material_recovery_percent_raw`, `product_sum_yield_percent_raw`, `mass_balance_sum_percent`, `starting_material_gt_100`, `mass_balance_gt_100`, `pressure_kpa_raw` | `solvent_b_fraction`, `temperature_c`, `residence_time_s`, `residence_time_min` | `total_product_yield_percent` |
| `nano-c-n-photochemistry-yield-percent` | `reactant-1`, `reactant-2`, `catalyst-1`, `catalyst-2`, `catalyst-3`, `catalyst-4`, `solvent-1`, `solvent-2`, `solvent-3`, `product` | `temperature_c`, `reaction_time_s`, `illumination_wavelength_nm`, `reflux_value` | `yield_percent` |
| `nicolit-nickel-coupling-yield-percent` | `reactant-1`, `reactant-2`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `pfizer-hte-lc-area-percent` | `reactant-1`, `reactant-2`, `reactant-3`, `reagent-1`, `reagent-2`, `reagent-3`, `reagent-4`, `reagent-5`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `product` | — | `lc_area_percent` |
| `photocatalytic-aryl-bromide-dehalogenation-conversion-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `catalyst-2`, `catalyst-3`, `solvent-1`, `solvent-2` | `reaction_time_s`, `illumination_wavelength_nm` | `conversion_percent` |
| `roche-borylation-yield-percent` | `reactant-1`, `reagent-1`, `reagent-2`, `reagent-3`, `reagent-4`, `reagent-5`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `science-hte-relative-lc-area-ratio` | `reactant-1`, `reactant-2`, `reactant-3`, `reagent-1`, `reagent-2`, `catalyst-1`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4` | `reaction_time_s` | `relative_product_lc_area_ratio` |
| `shields-arylation-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `catalyst-2`, `solvent-1`, `product` | `temperature_c`, `reaction_time_s` | `yield_percent` |
| `suzuki-miyaura-nanoscale-yield-percent` | `reactant-1`, `reactant-2`, `reagent-1`, `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `solvent-6`, `solvent-7`, `product` | `temperature_c`, `pressure_kpa`, `reaction_time_s`, `conditions_are_dynamic_value` | `yield_percent` |

## Integrity, licenses, and maintenance

- Data derivatives: CC BY-SA 4.0. Pipeline code: Apache-2.0. See `LICENSE-DATA`, `LICENSE-CODE`, `NOTICE`, and `CITATION.cff`.
- From the corpus release root, run `sha256sum -c SHA256SUMS`; every package also has its own `checksums.csv`.
- The machine-readable catalog is [`datasets/catalog.csv`](datasets/catalog.csv), the source manifest is [`provenance/source-files.csv`](provenance/source-files.csv), and compact two-hop row-lineage indexes and examples are in [`provenance/row-lineage/`](provenance/row-lineage/).
- Input boundaries, build history, and acceptance evidence are documented in [`SOURCE_BOUNDARIES.md`](SOURCE_BOUNDARIES.md), [`project-docs/buildlog.md`](project-docs/buildlog.md), and [`reports/release-acceptance/`](reports/release-acceptance/).
- This release does not claim that every model-ready target is an accepted public benchmark. Read its readiness status and label unit before use.

Maintainers can run:

```bash
python3 -m unittest discover -s pipeline/tests
```
