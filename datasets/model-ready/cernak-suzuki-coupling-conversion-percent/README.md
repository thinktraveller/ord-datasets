# Cernak Suzuki-Coupling Conversion (%)

[中文](README-zh.md)

This is an ORD subset prepared for direct reaction modelling. Its main table is
[`cernak-suzuki-coupling-conversion-percent-dataset.csv`](cernak-suzuki-coupling-conversion-percent-dataset.csv). The CSV bytes are identical to `dataset.csv` in the immutable
[`v0.1.0-model-ready-preview-1`](https://github.com/thinktraveller/ord-datasets/releases/tag/v0.1.0-model-ready-preview-1)
release; this directory uses a semantic filename to make individual downloads easier to identify.

## At a glance

| Item | Details |
|---|---|
| Main data file | [`cernak-suzuki-coupling-conversion-percent-dataset.csv`](cernak-suzuki-coupling-conversion-percent-dataset.csv) |
| Included / excluded / input records | 1,320 / 120 / 1,440 |
| Label column | `conversion_percent` |
| Label meaning and unit | percent conversion |
| Label-selection policy | `unique_structured_scalar_no_aggregation` |
| Modelling/benchmark readiness | `generated_pending_campaign_evaluation` |
| Data licence | `CC-BY-SA-4.0` |
| Associated publication | [10.1038/s44160-023-00351-1](https://doi.org/10.1038/s44160-023-00351-1) |

> “Model-ready” means that the file can be read and modelled directly. It does not mean that the target is an accepted general-purpose benchmark. Consider the readiness state and label meaning before modelling or comparing results.

## Chemical scope and filtering

Conversion modelling for miniaturised Suzuki coupling of aryl halides with boronic acids or boronate esters. The combinations span aryl-halide cores, boron partners, palladium precatalysts, bases, and solvents, enabling study of catalyst-substrate matching.

- This target uses only the ORD physical sources listed below.
- Only records satisfying `unique_structured_scalar_no_aggregation` are included; multiple candidate labels are never averaged or aggregated without an explicit rule.
- Observed exclusions: `non_finite_label`: 120 record(s)
- `audit.jsonl` preserves the label candidates, final decision, and rationale for every reaction. `exclusions.csv` preserves the records that did not enter the main table.

## Columns

| Field role | Columns |
|---|---|
| Reactants | `reactant-1`, `reactant-2` |
| Reagents, catalysts, solvents, and other components | `reagent-1`, `reagent-2`, `reagent-3`, `catalyst-1`, `solvent-1`, `solvent-2`, `solvent-3`, `solvent-4`, `solvent-5`, `solvent-6`, `solvent-7` |
| Products | None |
| Conditions | `reaction_time_s`, `reflux_value`, `conditions_are_dynamic_value` |
| Label | `conversion_percent` |

[`schema.json`](schema.json) is authoritative for the complete column order, units, and roles. Molecular-structure columns normally use SMILES; condition-column names carry their units, such as `_c`, `_s`, `_kpa`, or `_nm`.

## Files

| File | Purpose |
|---|---|
| [`cernak-suzuki-coupling-conversion-percent-dataset.csv`](cernak-suzuki-coupling-conversion-percent-dataset.csv) | Analysis-ready main table; each row is an included reaction. |
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

1. Select a row in [`cernak-suzuki-coupling-conversion-percent-dataset.csv`](cernak-suzuki-coupling-conversion-percent-dataset.csv). Its CSV row number, counting the header as row 1, is the `csv_row_number` in `row-map.csv`.
2. Find that number in [`row-map.csv`](row-map.csv) to obtain `physical_dataset_id`, `source_row_index`, and `label_decision_id`.
3. Search [`audit.jsonl`](audit.jsonl) for `label_decision_id` to see why the label was included or excluded.
4. Use `physical_dataset_id` in [`source-links.json`](source-links.json) to find the pinned ORD Parquet URL, revision, and SHA-256.
5. Use `physical_dataset_id` plus `source_row_index` to locate the same reaction in the complete ORD corpus. Do not rely on row order or SMILES alone.

## Pinned data sources

- `ord_dataset-3b8a2ef300e145468579027f206a3ac8`: [data/3b/ord_dataset-3b8a2ef300e145468579027f206a3ac8.parquet](https://github.com/open-reaction-database/ord-data/blob/83f971f586f6ad18f358ae4ae99d045e94ed2066/data/3b/ord_dataset-3b8a2ef300e145468579027f206a3ac8.parquet)  (ORD revision `83f971f586f6ad18f358ae4ae99d045e94ed2066`; SHA-256 `f8438f4490541ecd38d92208decc48ff33424d52772cc42701b7eb886fc14b8a`)

For a paper, report, or reproducible workflow, keep `metadata.json`, `source-links.json`, `row-map.csv`, and `checksums.csv` with the main table and cite the immutable release above. The data and derived metadata are CC BY-SA 4.0; retain attribution, source, and licence information.
