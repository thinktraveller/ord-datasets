# Processing pipeline

This directory will contain the versioned scripts, tests, policies, schemas,
configurations, workflows, and dependency locks required to reproduce a release.

Pipeline commands must accept source and output roots as parameters. Executable
configuration must not contain workstation-specific absolute paths, and source
roots must be treated as read-only.
