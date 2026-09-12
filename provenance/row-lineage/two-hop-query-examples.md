# Two-hop lineage query

1. For a corpus row, use `physical_dataset_id` and `source_file` in `reactions.csv` to select its dataset `source-links.json`; for a model-ready row, use the corresponding fields in `row-map.csv` or `exclusions.csv`.
2. Match that physical ID in `provenance/source-files.csv` to obtain the fixed upstream URL, Parquet SHA-256, source reaction count and ORD reaction identifier/row index.
