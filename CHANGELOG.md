# Changelog

All notable changes to Self-Evolving Software will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- LLM Conversational Layer (`/api/v1/chat/`) for interactive Q&A
- Configuration Abstraction Layer for framework-agnostic initialization
- New database models: Snapshot, HealthRecord, ForecastRecord
- Automated test infrastructure (pytest + vitest)
- Frontend component tests with API mocking

### Changed

- Updated Project model to use database relationships
- Improved project isolation in API endpoints

### Fixed

- Fixed project ID validation in API endpoints

## [0.1.0] - 2024-01-15

### Added

- Initial release of Self-Evolving Software
- Architecture health engine with stability analysis
- Forecasting engine with confidence scoring
- Behavior snapshot capture and storage
- Project-based data isolation
- REST API endpoints:
  - `/api/v1/health/` - Architecture health
  - `/api/v1/forecast/` - Health forecasting
  - `/api/v1/impact/` - Impact analysis
  - `/api/v1/graph/` - Architecture graph
  - `/api/v1/executive/` - Executive summary
  - `/api/v1/projects/` - Project management
- React dashboard with live metrics visualization

[Unreleased]: https://github.com/dummy-pranjal29/self-explaining-software/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dummy-pranjal29/self-explaining-software/releases/tag/v0.1.0
