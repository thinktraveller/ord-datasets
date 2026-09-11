# Semantic dataset-naming policy

Logical and physical identifiers are immutable machine identities. They stay in
catalog, provenance, source links, membership records, checksums and row
lineage; they are not sufficient public directory names.

For each corpus directory, this project assigns one stable lowercase kebab-case
`directory_slug` from frozen ORD dataset name/description, logical membership,
and shared DOI or upstream-source evidence. A merged logical dataset receives a
shared campaign/publication theme only when its member metadata supports it.
The name must not claim a reaction family, target, measurement, author or
benchmark completion state that lacks frozen evidence.

The semantic map must preserve all original IDs as aliases, be one-to-one with
logical datasets, cover each physical ID exactly once, avoid case-insensitive
slug collisions, and avoid UUID-only top-level names. Ambiguous cases are
marked `needs_manual_name_review`; they cannot be promoted to a final corpus
directory on an inferred name alone.
