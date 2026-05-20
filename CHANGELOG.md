# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- F-lite security: `pip-audit` CI job; Dependabot security update PRs enabled
- Community health files, CI, docs site, PyPI release workflow

## [0.1.0] - 2026-05-19

### Added

- Initial `mapsnatch` CLI: list and bulk-export maps via MindMeister public API
- Formats: FreeMind (`.mm`), PDF, `.mind`, XMind, RTF
- `--dry-run`, `--list-formats`, `.env` / env token support
- Tests with mocked HTTP (`pytest`, `responses`)

[Unreleased]: https://github.com/gavinc/mapsnatch/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gavinc/mapsnatch/releases/tag/v0.1.0
