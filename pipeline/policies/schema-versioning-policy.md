# Schema versioning policy

## Scope

This policy applies to every contract listed in
`pipeline/schemas/schema-index.json`: JSON documents, CSV headers, and their
field definitions. Contract versions use `MAJOR.MINOR.PATCH` and are carried in
each generated document as `schema_version` (or in a CSV sidecar manifest).

## Compatibility rules

| Change | Required version change | Migration rule |
|---|---|---|
| Remove or rename a field; change a type, unit, identifier, hash algorithm, URL pinning rule, or semantic meaning; make an optional field required | MAJOR | Keep the prior schema and a converter; do not overwrite existing metadata in place. |
| Add an optional field, enum value, optional record variant, or non-breaking validation rule | MINOR | Readers of the prior minor version must still parse old records. |
| Clarify descriptions, examples, or documentation without altering validation or meaning | PATCH | Existing artifacts remain valid without regeneration. |

The current frozen family is `1.1.0`; `1.0.0` remains valid for artifacts that
do not use target-specific optional CSV columns. Version 1.1.0 adds the
optional `campaign_id` row-map field and is backward compatible. A future release manifest records the
exact contract versions it uses; validation must select the matching version,
not silently use the newest schema.

## Immutability and review

- Once a data-moving step begins, a published schema file is immutable. A
  correction creates a new versioned file and records the supersession in the
  transformation graph.
- CSV column order is part of its contract. New optional columns are appended;
  a changed order is a MAJOR change.
- `null` means intentionally unknown or not applicable only where the schema
  explicitly permits it. Empty strings never stand in for `null`.
- A pinned source URL must contain a 40-hex Git revision. Branch, tag, and
  `main` URLs are invalid release provenance regardless of their availability.
- A schema change needs one valid fixture, one rejected fixture for its new
  guard, a version decision, and a passing full-contract test before it can be
  used by a build step.

## Release handling

Schema documents and the field dictionary are control-plane artifacts. They
are committed with small metadata, while data payloads remain subject to the
separate license, sensitive-data, storage, and release gates.
