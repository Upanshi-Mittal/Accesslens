# Changelog

All notable changes to the AccessLens Backend system will be documented in this file.

## [1.1.0] - Phase 5 Optimizations
### Added
- Complete Prometheus metrics exporting inside `AuditOrchestrator` (`AUDIT_REQUESTS` and `AUDIT_DURATION`).
- Database schema indexes to optimize queries on large report outputs (`002_add_indices.sql`).
- Asynchronous task queue table definitions (`003_add_audit_queue.sql`).
- Comprehensive markdown documentation (`ARCHITECTURE.md`, `API.md`, `CONTRIBUTING.md`).

### Changed
- Refactored `contrast_engine` and `structural_engine` to defer `window.getComputedStyle()` calls directly, maximizing rendering loop performance.
- Upgraded `cleanup.sh` to support headless CLI bypass flags (`--cache`, `--db`, `--reports`).

## [1.0.0] - Initial Hardened Release
### Added
- Fully determinative `wcag_engine` utilizing an `axe-core` bridge in Python.
- Multi-modal LLaVA and Mistral evaluations handling visual hierarchy gaps.
- SSRF protections and IP restriction matrices via `routes.py`.
- In-memory duplicate request cache blocking identical DoS payloads.
