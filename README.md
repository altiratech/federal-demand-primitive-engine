# Federal Demand Primitive Engine

Federal Demand Primitive Engine is a narrow federal demand-analysis repo focused on extracting reusable requirement kernels from public solicitation artifacts.

It starts with a `federal_spec_decompiler` wedge rather than a broad federal market-intelligence platform.

## Product Center

The founding loop is:
1. ingest one narrow solicitation corpus
2. extract recurring requirement kernels
3. normalize them into reusable demand primitives
4. expose evidence-backed outputs for product and venture decisions

## Status

Fresh scaffold.

The current purpose of the repo is to establish:
- founding docs
- implementation guardrails
- source and evidence boundaries
- the intended repo shape for the first extraction loop

No broad runnable product surface is expected yet.

## Canonical Build Truth

Treat these docs as authoritative:
- `docs/FOUNDING_PACKET.md`
- `docs/DEVELOPMENT_PACKET.md`
- `docs/BOOTSTRAP.md`
- `docs/FIRST_SLICE.md`
- `docs/IMPLEMENTATION_ENTRY_BRIEF.md`
- `docs/ARCHITECTURE_GUARDRAILS.md`

## Planned Repo Shape

```text
configs/         source definitions, corpus rules, and rubric versions
data/            raw pulls, snapshots, staging, and canonical layers
pipeline/        ingest, normalize, extract, score, and publish logic
artifacts/       kernel payloads and site outputs
apps/api/        thin API or orchestration surface when needed
apps/web/        kernel explorer and evidence UI
packages/shared/ shared contracts and schemas
docs/            build truth and guardrails
```

## Build Rule

Do not attempt to build the full federal demand platform first. Build the decompiler wedge, prove the kernel extraction loop, then expand.

## License

No open-source license has been selected yet. Public source visibility does not grant reuse rights until a license file is added.
