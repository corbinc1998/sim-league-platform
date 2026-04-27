# 0001 — Project structure and tooling

**Status:** Accepted
**Date:** 2026-04-23

## Context

sim-league-platform is a Python ETL and analytics platform that will grow to include multiple data sources, two persistent stores (Postgres and MongoDB), workflow orchestration (Prefect), and an HTTP API (FastAPI). The codebase needs to support clean evolution — adding new data sources, swapping persistence layers, and migrating logic between systems — without business logic becoming entangled with infrastructure.

The decisions in this ADR were made before any business logic was written, so the project starts the way it should continue.

## Decision

### 1. `src/` layout

The Python package lives at `src/sim_league_platform/` rather than at the project root. Tests live at `tests/` and import the package as installed.

**Rationale:** prevents accidental imports of uninstalled local files, forces tests to run against the actually-installed package (catches packaging bugs early), and matches the layout of mature Python projects.

### 2. Ports and adapters (hexagonal) architecture

Code is organized into three layers:
- `domain/` — pure business logic with no IO. Defines protocols (ports) for external dependencies.
- `adapters/` — concrete implementations of those ports: Postgres repositories, Mongo repositories, OCR input handlers, HTTP clients.
- `flows/` and `api/` — composition roots that wire adapters to domain code.

**Rationale:** the platform will undergo at least two known migrations during its lifetime — Postgres-only to Postgres+Mongo, and synchronous ingestion to scheduled flows. Ports and adapters localize the cost of these migrations to the adapter layer. Domain code remains unchanged.

This pattern also makes the domain trivially testable without mocks or test doubles for infrastructure.

### 3. Strict typing from day one

`mypy` runs in `--strict` mode in CI. The configuration applies to both `src/` and `tests/`.

**Rationale:** strict typing is dramatically cheaper to adopt early than to retrofit. It catches an entire class of bugs at edit time rather than at runtime, and it produces a codebase that is easier to refactor with confidence — directly supporting the migration work this platform will undertake.

### 4. Tooling: uv, ruff, pytest, pytest-cov

- **uv** for dependency management and virtual environments (faster than Poetry, single tool, lockfile-first).
- **ruff** for linting and formatting (replaces black, flake8, isort with a single fast tool).
- **pytest** as the test runner; **pytest-cov** for coverage reporting.

**Rationale:** modern, fast, low-ceremony tooling reduces friction in a solo project and matches what a pragmatic engineering team would adopt today.

## Consequences

- New contributors (or the author returning to the project) have a clear, conventional structure to navigate.
- Adding a new persistence layer or data source means writing a new adapter, not refactoring domain code.
- The strict mypy configuration will occasionally require explicit type annotations that feel verbose, particularly around third-party libraries without type stubs. This cost is accepted as a trade-off for the long-term refactoring confidence it provides.
- Test execution is slightly slower than a flat layout because the package must be installed (in editable mode) before tests can run. Acceptable.

## References

- [The src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) — Python Packaging Authority
- [Hexagonal architecture](https://alistair.cockburn.us/hexagonal-architecture/) — Alistair Cockburn
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — Michael Nygard