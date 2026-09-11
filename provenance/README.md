# Provenance

This directory will describe four connected provenance levels:

1. source files and immutable upstream revisions;
2. physical, logical, package, and target datasets;
3. transformation steps and artifact hash edges;
4. row-level mappings back to physical dataset, source row, and reaction ID.

No provenance record is considered active until its schema and link/hash checks
pass the corresponding project-plan gate.
