# Asymmetric Alkylation ee (S-R, %)

[中文](README-zh.md)

This is an ORD subset prepared for direct reaction modelling. Its main table is
[`asymmetric-alkylation-ee-s-minus-r-percent-dataset.csv`](asymmetric-alkylation-ee-s-minus-r-percent-dataset.csv). The CSV bytes are identical to `dataset.csv` in the immutable
[`v0.1.0-model-ready-preview-1`](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1)
release; this directory uses a semantic filename to make individual downloads easier to identify.

## At a glance

| Item | Details |
|---|---|
| Main data file | [`asymmetric-alkylation-ee-s-minus-r-percent-dataset.csv`](asymmetric-alkylation-ee-s-minus-r-percent-dataset.csv) |
| Included / excluded / input records | 1,430 / 0 / 1,430 |
| Label column | `ee_s_minus_r_percent` |
| Label meaning and unit | percentage points, S minus R |
| Label-selection policy | `signed_selectivity_v1:s_config_imms_percentage` |
| Modelling/benchmark readiness | `generated_adapter_blocked` |
| Data licence | `CC-BY-SA-4.0` |
| Associated publication | [10.1038/s41467-023-42446-5](https://doi.org/10.1038/s41467-023-42446-5) |

> “Model-ready” means that the file can be read and modelled directly. It does not mean that the target is an accepted general-purpose benchmark. Consider the readiness state and label meaning before modelling or comparing results.

## Chemical scope and filtering

Enantioselectivity modelling for photoredox/organocatalytic aldehyde alpha-asymmetric alkylation. The label is signed ee (S minus R, percentage points), not yield; product stereochemistry is used only to determine the label, not as a model feature.

- This target uses only the ORD physical sources listed below.
- Only records satisfying `signed_selectivity_v1:s_config_imms_percentage` are included; multiple candidate labels are never averaged or aggregated without an explicit rule.
- Observed exclusions: No additional exclusions.
- `audit.jsonl` preserves the label candidates, final decision, and rationale for every reaction. `exclusions.csv` preserves the records that did not enter the main table.

## Columns

| Field role | Columns |
|---|---|
| Reactants | `reactant-1`, `reactant-2`, `reactant-3` |
| Reagents, catalysts, solvents, and other components | `catalyst-1`, `catalyst-2`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5` |
| Products | None |
| Conditions | None |
| Label | `ee_s_minus_r_percent` |

[`schema.json`](schema.json) is authoritative for the complete column order, units, and roles. Molecular-structure columns normally use SMILES; condition-column names carry their units, such as `_c`, `_s`, `_kpa`, or `_nm`.

## Files

| File | Purpose |
|---|---|
| [`asymmetric-alkylation-ee-s-minus-r-percent-dataset.csv`](asymmetric-alkylation-ee-s-minus-r-percent-dataset.csv) | Analysis-ready main table; each row is an included reaction. |
| [`schema.json`](schema.json) | Exact columns, field roles, label definition, and extraction rule. |
| [`row-map.csv`](row-map.csv) | Maps a main-table row to its ORD reaction record. |
| [`audit.jsonl`](audit.jsonl) | Records the label candidates, selected value, and reason for every decision. |
| [`exclusions.csv`](exclusions.csv) | Lists records excluded from the main table and the reason for each decision. |
| [`source-links.json`](source-links.json) | Commit-pinned ORD source links and SHA-256 values. |
| [`metadata.json`](metadata.json) | Dataset identity, size, label unit, licence, and readiness state. |
| [`yonod-config.json`](yonod-config.json) | Configuration for [YONOD](https://github.com/thinktraveller/YONOD): maps table columns to model roles and includes an example setup; optional for manual analysis. |
| [`target-build-provenance.json`](target-build-provenance.json) | Input files, transformation rules, and hashes used to build this target; use it to reproduce or audit the build. |
| [`checksums.csv`](checksums.csv) | File paths, SHA-256 fingerprints, and sizes for checking download integrity or unexpected changes. |

## Trace one reaction

1. Select a row in [`asymmetric-alkylation-ee-s-minus-r-percent-dataset.csv`](asymmetric-alkylation-ee-s-minus-r-percent-dataset.csv). Its CSV row number, counting the header as row 1, is the `csv_row_number` in `row-map.csv`.
2. Find that number in [`row-map.csv`](row-map.csv) to obtain `physical_dataset_id`, `source_row_index`, and `label_decision_id`.
3. Search [`audit.jsonl`](audit.jsonl) for `label_decision_id` to see why the label was included or excluded.
4. Use `physical_dataset_id` in [`source-links.json`](source-links.json) to find the pinned ORD Parquet URL, revision, and SHA-256.
5. Use `physical_dataset_id` plus `source_row_index` to locate the same reaction in the complete ORD corpus. Do not rely on row order or SMILES alone.

## Pinned data sources

- `ord_dataset-c5b00523487a4211a194160edf45e9ab`: [data/c5/ord_dataset-c5b00523487a4211a194160edf45e9ab.parquet](https://github.com/open-reaction-database/ord-data/blob/83f971f586f6ad18f358ae4ae99d045e94ed2066/data/c5/ord_dataset-c5b00523487a4211a194160edf45e9ab.parquet)  (ORD revision `83f971f586f6ad18f358ae4ae99d045e94ed2066`; SHA-256 `73c04ce2acaf6cf2b6b3ecda8c623d2a321435f1f5830aedb0a0f1afd562bdc4`)

For a paper, report, or reproducible workflow, keep `metadata.json`, `source-links.json`, `row-map.csv`, and `checksums.csv` with the main table and cite the immutable release above. The data and derived metadata are CC BY-SA 4.0; retain attribution, source, and licence information.
