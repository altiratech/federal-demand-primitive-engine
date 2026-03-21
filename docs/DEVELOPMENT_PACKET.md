# Federal Demand Primitive Engine Development Packet

Status: hydrated repo-local build packet

## Purpose

This file consolidates the richer source material behind this repo so development can proceed inside the repo without reopening the Karpathy source folders for the core product thesis, source inventory, schema logic, UI direction, or execution plan.

## Source Materials Absorbed

- `Business Ideas/01_Karpathy/KarpathyMerged/app_ideas_catalog.md`
- `Business Ideas/01_Karpathy/KarpathyMerged/evaluation_results.md`
- `Business Ideas/01_Karpathy/KarpathyMerged/merged_concepts.md`
- `Business Ideas/01_Karpathy/KarpathyMerged/implementation_blueprint.md`
- `Business Ideas/01_Karpathy/KarpathyMerged/karpathy1_idea_lineage.md`

## Product Thesis

Merge white-space radar, pre-RFP demand detection, and spec decompilation into a federal demand engine that identifies future demand and the recurring requirement kernels worth building around.

Important founding constraint:
- the repo must not start at full merged scope
- the required first wedge is `federal_spec_decompiler`

## Why This Exists

- notices and awards alone are too reactive
- requirement kernels are often where reusable product strategy emerges
- venture formation, GTM, and product selection all improve if recurring federal burdens are made inspectable

## First Users

Primary early users:
- govtech founders
- venture-style builders
- acquisition entrepreneurs
- BD or solution-architecture operators exploring one narrow wedge

## Job To Be Done

See which recurring procurement burdens appear across a narrow agency/problem family and decide which primitive is worth building around.

## Canonical Object

Primary object:
- `requirement_kernel`

Supporting units:
- source document
- document section
- kernel cluster
- related opportunity context

This repo is not centered on:
- a generic opportunity row
- a giant award dashboard
- broad procurement workflow software

## Parent Ideas Preserved Here

### `federal_contract_white_space_radar`
Adds:
- underserved demand framing
- supplier-thin demand pockets
- commercial or venture-formation logic

### `pre_rfp_demand_detector`
Adds:
- timing and lifecycle sensitivity
- re-compete and latent-demand logic
- not-yet-obvious demand framing

### `federal_spec_decompiler`
Adds:
- recurring requirement-kernel extraction
- evidence-grounded ontology
- the actual required MVP wedge for this repo

## Narrow Starting Wedge

Start with:
- one agency cluster
- one problem family
- one repeatable requirement taxonomy
- roughly 100-300 solicitations or related documents in one narrow corpus

Do not start with:
- broad multi-agency market coverage
- general federal whitespace mapping
- full pre-RFP prediction
- full federal intelligence sprawl

## Data Source Inventory

First-tier wedge sources:
- SAM.gov Get Opportunities Public API
  - primary solicitation corpus
- USAspending API
  - related award context and demand history
- SAM.gov Contract Awards API
  - adjacent contract context where available

Important later overlays:
- Federal Register
  - policy and rule context for specific clusters
- SBA Small Business Search
  - supplier-density and ecosystem context
- SBIR/STTR API
  - optional innovation/prototype overlay, not a blocking dependency

## Data Truth Rules

- use official sources only
- prefer APIs and official bulk docs over scraping
- keep source documents, normalized text, kernels, and scored outputs in separate layers
- kernels are inferred, source clauses are observed
- every kernel must link back to evidence snippets
- never fabricate solicitations, agencies, dates, or award context

## Canonical Schema

### `documents`
- `document_id`
- `source_system`
- `agency_code`
- `opportunity_id`
- `title`
- `published_at`
- `raw_path`
- `source_url`

### `document_sections`
- `section_id`
- `document_id`
- `section_key`
- `section_title`
- `section_text`
- `offset_start`
- `offset_end`

### `requirement_kernels`
- `kernel_id`
- `kernel_label`
- `kernel_family`
- `problem_family`
- `normalized_requirement`
- `cluster_id`
- `evidence_count`

### `kernel_evidence`
- `evidence_id`
- `kernel_id`
- `document_id`
- `section_id`
- `snippet_text`
- `snippet_role`
- `source_url`

### `kernel_scores`
- `score_id`
- `kernel_id`
- `recurrence_score`
- `margin_potential`
- `implementation_burden`
- `ai_automation_leverage`
- `compliance_burden`
- `cross_domain_reuse`
- `confidence`
- `rationale`
- `rubric_version`

### `opportunity_context`
- `context_id`
- `kernel_id`
- `agency_code`
- `related_award_count`
- `related_opportunity_count`
- `time_window`

## Scoring Model

Core wedge dimensions from `federal_spec_decompiler`:
- recurrence across agencies or documents
- margin potential
- implementation burden
- AI automation leverage
- compliance burden
- cross-domain reuse

Expansion dimensions preserved from the parent ideas:
- winnability
- time-to-cash
- teaming potential
- predictability
- likely recompete timing
- set-aside opening

Working rule:
- the wedge starts with kernel usefulness, not a giant blended score across every federal concept

## UI Guidance

Primary expression:
- taxonomy tree or kernel explorer

Secondary views:
- evidence panel
- corpus search
- kernel detail page
- related opportunity context

Not the right first product:
- generic federal dashboard
- bid-management interface
- giant list of notices with weak ontology

## First User Workflow

1. search a narrow requirement cluster
2. inspect repeated compliance or capability kernels
3. read the source snippets behind each kernel
4. decide whether a reusable product or service can satisfy that recurring burden

## MVP Build Sequence

Phase 0:
- choose the first agency cluster
- choose the first problem family
- define the first repeatable taxonomy

Phase 1:
- ingest and cache a narrow solicitation corpus
- keep request metadata and raw text immutable

Phase 2:
- normalize source text into sections and comparable clauses
- extract recurring requirement statements

Phase 3:
- cluster and label kernels
- store linked evidence snippets
- score the kernel set

Phase 4:
- build a kernel explorer with search and evidence drill-down
- show frequency and related opportunity context

Phase 5:
- test whether the taxonomy is reusable enough to justify expansion

## MVP Success Definition

The MVP works when a serious federal-market builder can:
- inspect one narrow corpus
- see repeated requirement kernels with evidence
- understand which kernels are common enough to build around
- leave with a believable build-here or monitor-here thesis

## Key Risks

Ontology and language risks:
- federal language variance creates false novelty
- weak sectioning or clustering will create fake kernels
- users may not buy into kernel thinking unless the evidence is extremely clear

Scope risks:
- the repo can drift into generic federal market intelligence very quickly
- adding multiple agencies or multiple problem families too early will destroy clarity

Operational risks:
- API friction or source cadence may be annoying
- some useful signals may live outside the first wedge and tempt premature expansion

## Validation Checklist

1. Confirm the first agency cluster.
2. Confirm the first problem family.
3. Validate 20-30 documents for sectioning and repeated-kernel quality.
4. Test whether a small kernel library feels more useful than a list of notices.
5. Validate that one repeatable taxonomy survives document variation.
6. Only then expand into whitespace or pre-RFP overlays.

## Placeholder Rule

Use:
- empty kernel arrays
- explicit `source_status`
- explicit confidence and unknowns

Do not use:
- synthetic solicitations
- fake agency histories
- invented award context

## Local Repo Translation

Current local scaffold:
- `apps/api/`
- `apps/web/`
- `packages/shared/`
- `docs/`
- `scripts/`
- `tests/`

Recommended implementation expansion:
- `configs/`
  - source definitions and rubric versions
- `data/`
  - raw, snapshots, staging, canonical
- `pipeline/`
  - ingest, normalize, extract, score, publish
- `artifacts/`
  - kernel payloads and site outputs

Working rule:
- `apps/api` should stay thin and only expose or orchestrate the kernel engine
- the real product truth should live in data, pipeline, configs, and artifacts
