# Corpus semantic-name review

## Result

The frozen metadata supports approved human-readable names for all 41
logical corpus datasets. The map covers 53 physical IDs and
2,428,291 reactions. There are no slug collisions and no UUID-only
top-level directory names. IDs remain in metadata and provenance; only directory labels become semantic.

## Naming policy

- Prefer the frozen physical dataset name and description.
- For a merged logical dataset, use the shared publication or upstream campaign identity and a reaction
  theme present in its member metadata.
- Use a stable lowercase kebab-case slug. A DOI or upstream key is retained as an alias and is added to a
  slug only when otherwise necessary for disambiguation.
- Do not invent reaction class, yield meaning, author attribution, or a benchmark status not recorded by
  the frozen manifests.

## Validation

- logical map rows: 41
- covered physical IDs: 53
- reaction-count sum: 2,428,291
- relationship counts: {"independent": 33, "same_publication": 6, "same_upstream_source": 2}
- slug collisions: 0
- manual-review rows: 0

The full mapping, aliases, member IDs, fixed source paths, DOI/upstream evidence and planned corpus
locations are in provenance/semantic-name-map.csv.
