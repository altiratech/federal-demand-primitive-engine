# Federal Demand Primitive Engine Bootstrap Contract

Status: locked for scaffold-phase kickoff

## Toolchain Decision

- Python work uses the shared fastlane environment at `/Users/ryanjameson/Desktop/Lifehub/.venv-fastlane`.
- JavaScript work uses `npm` only after real code lands in `apps/web` or `packages/shared`.
- Slice 1 is Python-first and local-only.
- Slice 1 does not require a database or deployment target.

## Start Rule

1. Start in `configs/`, `pipeline/`, and `artifacts/`.
2. Keep `apps/web` parked until there is one inspectable kernel payload.
3. Add `packages/shared` only when both extraction and UI need the same contract.

## First Executable Contract

Before any UI work, produce:
- one narrow corpus definition
- one immutable raw text cache under `data/`
- one normalized section model
- one kernel artifact payload under `artifacts/`

## Explicit Defers

Do not start with:
- `npm install`
- award analytics
- background workers
- a database
- deployment setup
