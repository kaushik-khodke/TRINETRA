# Implementation Package Instructions

This folder is an IDE-ready handoff for the satellite research workspace.

## Files

- `implementation-plan.md` — complete product, architecture, API, database, pipeline, security, testing, deployment, copilot, COG rendering, and UI plan.
- `schema.sql` — PostgreSQL/PostGIS starter schema.
- `copilot-prompt-and-validation.md` — prompt engineering, strict JSON planning, validation, approval, and adversarial test guidance.
- `cog-rendering-stack.md` — frontend COG rendering stack and large-raster performance rules.
- `examples/analysis-plan.valid.json` — valid typed plan.
- `examples/analysis-plan.blocked.json` — intentionally blocked plan showing safe validation behavior.
- `examples/pipeline-registry.json` — example allowlisted pipeline definitions.
- `examples/evidence-answer.json` — evidence-linked answer shape.

## Recommended implementation order

1. Read `implementation-plan.md`.
2. Apply `schema.sql` through the project's migration system.
3. Implement mission/AOI and permission boundaries.
4. Implement upload validation and COG normalization.
5. Implement STAC search and MapLibre rendering.
6. Implement the pipeline registry and three MVP workers.
7. Implement strict plan schema validation and domain validation.
8. Add copilot plan generation only behind the approval gate.
9. Add run monitoring, provenance, notebook entries, and exports.
10. Add the glassmorphism UI layer only after accessibility and map readability are verified.

## Local development target

Provide a local stack with:

- React/TypeScript web app.
- TypeScript API.
- PostgreSQL + PostGIS.
- S3-compatible object storage.
- Durable queue.
- Separate worker process.
- TiTiler service for server-side raster fallback.

## Required quality gates

- All API responses validated at runtime.
- All copilot plans validated structurally and against mission data.
- No worker run without an approved plan.
- No cross-mission object URL access.
- Geospatial golden tests for RGB, optical indices, SAR change, CRS, nodata, clipping, and COG validity.
- End-to-end test from question to reproducible export.
