# NiCOlit Nickel-Coupling Yield (%)

[中文](README-zh.md)

This is an ORD subset prepared for direct reaction modelling. Its main table is
[`nicolit-nickel-coupling-yield-percent-dataset.csv`](nicolit-nickel-coupling-yield-percent-dataset.csv). The CSV bytes are identical to `dataset.csv` in the immutable
[`v0.1.0-model-ready-preview-1`](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1)
release; this directory uses a semantic filename to make individual downloads easier to identify.

## At a glance

| Item | Details |
|---|---|
| Main data file | [`nicolit-nickel-coupling-yield-percent-dataset.csv`](nicolit-nickel-coupling-yield-percent-dataset.csv) |
| Included / excluded / input records | 1,669 / 93 / 1,762 |
| Label column | `yield_percent` |
| Label meaning and unit | percent yield as defined by the source measurement |
| Label-selection policy | `unique_structured_scalar_no_aggregation` |
| Modelling/benchmark readiness | `generated_with_source_caveat` |
| Data licence | `CC-BY-SA-4.0` |
| Associated publication | [10.1002/chem.201603436](https://doi.org/10.1002/chem.201603436) |

> “Model-ready” means that the file can be read and modelled directly. It does not mean that the target is an accepted general-purpose benchmark. Consider the readiness state and label meaning before modelling or comparing results.

## Chemical scope and filtering

Percent-yield modelling for nickel-catalysed organolithium cross-coupling involving C-O/C-N bond activation of ethers or aryl ammonium salts. Zero values are retained; GC and isolated yields are not distinguished and should be treated as an interpretation limitation.

- This target uses only the ORD physical sources listed below.
- Only records satisfying `unique_structured_scalar_no_aggregation` are included; multiple candidate labels are never averaged or aggregated without an explicit rule.
- Observed exclusions: `missing_desired_product`: 92 record(s); `missing_required_reactant_smiles`: 1 record(s)
- `audit.jsonl` preserves the label candidates, final decision, and rationale for every reaction. `exclusions.csv` preserves the records that did not enter the main table.

## Columns

| Field role | Columns |
|---|---|
| Reactants | `reactant-1`, `reactant-2` |
| Reagents, catalysts, solvents, and other components | None |
| Products | `product` |
| Conditions | `temperature_c`, `reaction_time_s` |
| Label | `yield_percent` |

[`schema.json`](schema.json) is authoritative for the complete column order, units, and roles. Molecular-structure columns normally use SMILES; condition-column names carry their units, such as `_c`, `_s`, `_kpa`, or `_nm`.

## Files

| File | Purpose |
|---|---|
| [`nicolit-nickel-coupling-yield-percent-dataset.csv`](nicolit-nickel-coupling-yield-percent-dataset.csv) | Analysis-ready main table; each row is an included reaction. |
| [`schema.json`](schema.json) | Exact columns, field roles, label definition, and extraction rule. |
| [`row-map.csv`](row-map.csv) | Maps a main-table row to its ORD reaction record. |
| [`audit.jsonl`](audit.jsonl) | Records the label candidates, selected value, and reason for every decision. |
| [`exclusions.csv`](exclusions.csv) | Lists records excluded from the main table and the reason for each decision. |
| [`source-links.json`](source-links.json) | Commit-pinned ORD source links and SHA-256 values. |
| [`metadata.json`](metadata.json) | Dataset identity, size, label unit, licence, and readiness state. |
| [`yonod-config.json`](yonod-config.json) | Model field roles and example configuration. |
| [`target-build-provenance.json`](target-build-provenance.json) | Hashes of the inputs and transformations used to build this target. |
| [`checksums.csv`](checksums.csv) | Checks whether data and provenance files are damaged or modified. |

## Trace one reaction

1. Select a row in [`nicolit-nickel-coupling-yield-percent-dataset.csv`](nicolit-nickel-coupling-yield-percent-dataset.csv). Its CSV row number, counting the header as row 1, is the `csv_row_number` in `row-map.csv`.
2. Find that number in [`row-map.csv`](row-map.csv) to obtain `physical_dataset_id`, `source_row_index`, and `label_decision_id`.
3. Search [`audit.jsonl`](audit.jsonl) for `label_decision_id` to see why the label was included or excluded.
4. Use `physical_dataset_id` in [`source-links.json`](source-links.json) to find the pinned ORD Parquet URL, revision, and SHA-256.
5. Use `physical_dataset_id` plus `source_row_index` to locate the same reaction in the complete ORD corpus. Do not rely on row order or SMILES alone.

## Pinned data sources

- `ord_dataset-9b8aa9a7835143ef8ce3f70abfab7545`: [data/9b/ord_dataset-9b8aa9a7835143ef8ce3f70abfab7545.parquet](https://github.com/open-reaction-database/ord-data/blob/83f971f586f6ad18f358ae4ae99d045e94ed2066/data/9b/ord_dataset-9b8aa9a7835143ef8ce3f70abfab7545.parquet)  (ORD revision `83f971f586f6ad18f358ae4ae99d045e94ed2066`; SHA-256 `195765643b4aaad79d9ed82de6737a4855b9f2716e0bc0aa10cff950b7604d39`)

For a paper, report, or reproducible workflow, keep `metadata.json`, `source-links.json`, `row-map.csv`, and `checksums.csv` with the main table and cite the immutable release above. The data and derived metadata are CC BY-SA 4.0; retain attribution, source, and licence information.
