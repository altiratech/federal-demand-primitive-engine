# Federal Demand Primitive Engine First Slice

Status: locked kickoff slice

## Goal

Extract recurring requirement kernels from one narrow SAM.gov solicitation corpus for one agency cluster and one problem family, then publish an evidence-first kernel library.

## Locked Decisions

- First agency cluster: Department of Veterans Affairs.
- First problem family: case-management and workflow-support solicitations.
- First corpus target: roughly 100-150 opportunity documents or related text artifacts.
- First UI mode: no web app until one inspectable kernel artifact exists.
- First taxonomy shape:
  - intake / routing
  - records / documentation
  - review / approval
  - reporting / compliance support

## First Source Set

- SAM.gov Get Opportunities Public API
- related solicitation text captured into immutable raw files

## First Files To Touch

- `configs/`
- `pipeline/`
- `data/`
- `artifacts/`
- `tests/`

## Done When

- the corpus can be fetched and cached repeatably
- sections can be normalized across varied document formats
- recurring kernels can be clustered with linked evidence snippets
- one artifact payload makes the kernel set more useful than a notice list

## Not Yet

- multi-agency expansion
- pre-RFP prediction
- broad whitespace radar
- full award overlays
