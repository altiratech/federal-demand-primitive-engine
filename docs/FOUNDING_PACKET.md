# Federal Demand Primitive Engine Founding Packet

Status: canonical current-scope document

## 1. Project

- Project name: Federal Demand Primitive Engine
- Owner: Ryan Jameson
- Date opened: 2026-03-20
- Status: scaffolded

## 2. One-Sentence Product Definition

`This product helps govtech founders and venture-style builders identify reusable requirement kernels in one narrow federal demand cluster using public solicitation text, without becoming a giant generic federal intelligence platform.`

## 3. First User

- Primary user: govtech founder or venture-style builder exploring one federal wedge
- What they are trying to get done: understand repeated requirement patterns worth productizing
- What they do today instead: manual solicitation reading and expert intuition
- Why they would switch: reusable kernels collapse large document sets into clearer product decisions

## 4. First Workflow

1. user loads a narrow corpus from one agency/problem family
2. user sees repeated requirement kernels extracted from source text
3. user inspects evidence snippets behind each kernel
4. user decides which primitive is worth building around

## 5. Canonical Object

- Canonical object: `requirement_kernel`
- Why this is the product center: the repo is about reusable demand primitives, not whole solicitations
- What is explicitly not the canonical object: award dashboard or generalized opportunity listing

## 6. Current Scope

- In scope:
  - one agency cluster
  - one requirement family
  - solicitation parsing
  - kernel extraction
  - evidence-backed taxonomy view

## 7. Explicit Non-Goals

- Not in scope now:
  - full federal demand platform
  - broad whitespace radar
  - pre-RFP prediction
  - full contract intelligence stack

## 8. Do-Not-Drift-Into

- Drift risks to avoid:
  - broad opportunity search product
  - procurement workflow software
  - analytics dashboard without reusable primitives

## 9. Approved Terminology

| Use | Avoid | Why |
|---|---|---|
| `requirement kernel` | `spec summary` | keeps focus on reusable primitives |
| `demand primitive` | `lead` | clarifies that the object is productizable demand |
| `evidence snippet` | `AI explanation` | keeps provenance primary |

## 10. Repo / Architecture Pattern

- Repo shape: standalone mono-repo scaffold
- Frontend stack: React + TypeScript
- Backend stack: Python-first ingest and extraction
- Shared contracts: `packages/shared`
- Deployment target: local-first until the primitive model proves useful
- Explicitly rejected patterns:
  - broad federal data platform
  - multi-agency sprawl before one corpus works

## 11. Data Truth Rules

- Source of truth: official federal solicitation/opportunity text
- What is observed vs inferred: source text is observed, kernels are inferred
- What can be missing: corpus breadth and agency coverage
- What must never be faked: solicitations, dates, agencies, or extracted evidence
- How uncertainty should be shown: evidence plus confidence

## 12. Quality Gates

- Required validation:
  - parser works on representative documents
  - kernels remain grounded in source snippets
  - one narrow corpus yields repeated useful primitives

## 13. First 2-4 Week Build Sequence

| Order | Build block | Why now |
|---|---|---|
| 1 | choose corpus and schema | prevents sprawl |
| 2 | parse and normalize text | source truth |
| 3 | extract and cluster kernels | core product value |
| 4 | evidence explorer UI | proves usefulness |

## 14. Open Questions That Do Not Block Start

- Open but non-blocking:
  - kickoff decisions are now locked in `docs/FIRST_SLICE.md`
  - whether award context is needed in v1 or can wait

## 15. Go / No-Go Check Before Real Code

- [x] one-sentence product definition is stable
- [x] first user is specific
- [x] first workflow is specific
- [x] canonical object is clear
- [x] non-goals are written down
- [x] terminology is coherent
- [x] repo pattern is chosen
- [x] data truth rules are defined
