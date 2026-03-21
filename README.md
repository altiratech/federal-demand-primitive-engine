# Federal Demand Primitive Engine

Federal Demand Primitive Engine is a standalone repo scaffold hydrated from the KarpathyMerged materials.

## Product Center

The founding build is not the full merged concept.

The repo must start as:
- a narrower `federal_spec_decompiler` wedge

That means:
1. ingest one narrow solicitation corpus
2. extract recurring requirement kernels
3. normalize them into reusable demand primitives
4. expose evidence-backed outputs for product and venture decisions

## Current Repo Status

This repo is a fresh scaffold for this product.

## Canonical Build Truth

Treat these docs as authoritative:
- `docs/FOUNDING_PACKET.md`
- `docs/DEVELOPMENT_PACKET.md`
- `docs/BOOTSTRAP.md`
- `docs/FIRST_SLICE.md`
- `docs/IMPLEMENTATION_ENTRY_BRIEF.md`
- `docs/ARCHITECTURE_GUARDRAILS.md`

## Planned Repo Shape

- `configs/`
  - source definitions, corpus selection rules, and rubric versions
- `data/`
  - raw pulls, snapshots, staging, and canonical data layers
- `pipeline/`
  - ingest, normalize, extract, score, and publish logic
- `artifacts/`
  - kernel payloads and site outputs
- `apps/api/`
  - thin API or orchestration surface when needed
- `apps/web/`
  - kernel explorer and evidence UI
- `packages/shared/`
  - shared contracts and schemas

## Build Rule

Do not attempt to build the full federal demand platform first.
Build the decompiler wedge, prove the kernel extraction loop, then expand.
