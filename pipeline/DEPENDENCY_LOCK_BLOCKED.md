# Dependency lock resolution

The initial step-19 attempt could not retrieve `ruff` because TLS connection
failed. Network access was subsequently restored and `uv lock` generated the
tracked `uv.lock` file.

The lock now includes the clean-room runtime dependencies `ord-schema` and
`pyarrow`, alongside the existing contract-validation and development tools.
Its verification command is:

```bash
uv sync --group dev --locked
uv run pytest -q
uv run ruff check scripts tests
```

The lock contains no credentials or workstation paths. The historical failed
attempt remains superseded by the complete step-19 acceptance report.
