# Reaction JSON email-redaction policy

## Scope

This policy applies before promoting any CSV with a `reaction_json` column from
the frozen legacy workspace into `intermediate/01-physical-csv/` or
`datasets/corpus/`. It was introduced after the step-07 scan found literal
email addresses in 53 physical exports and their 41 logical corpus tables.

## Deterministic rule

`pipeline/scripts/sanitize_reaction_json_csv.py` walks each JSON value in row
order. Any scalar string that exactly matches the project email pattern is
removed from a dictionary or list. The rule therefore covers both correctly
named `email` fields and malformed provenance `name` fields whose value is an
email address. It does not alter other strings, reaction identifiers, row
ordering, CSV columns, reaction JSON keys whose values are not emails, or
provenance timestamps.

## Required evidence for every promoted derivative

- input and output SHA-256;
- input/output row counts and unchanged CSV field order;
- only aggregate counts by JSON key path, never email values, snippets, or
  local source paths;
- a repeat scan with no remaining literal email match; and
- a transformation record that links the derivative to the frozen input hash.

No raw CSV that carries a step-07 `potential_personal_email` finding may enter
an upload allowlist. Keeping the frozen source hash and source-file links in
provenance preserves reproducibility without publishing the removed values.
