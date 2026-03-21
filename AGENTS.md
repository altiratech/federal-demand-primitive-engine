# Federal Demand Primitive Engine Agent Rules

Scope: `/Users/ryanjameson/Desktop/Lifehub/Code/active/KProject/federal-demand-primitive-engine`

## Mandatory Protocol

Always follow:
- `/Users/ryanjameson/Desktop/Lifehub/SYSTEM/SESSION_PROTOCOL.md`

## Current Build Truth

Use these files first:
- `docs/FOUNDING_PACKET.md`
- `docs/DEVELOPMENT_PACKET.md`
- `docs/BOOTSTRAP.md`
- `docs/FIRST_SLICE.md`
- `docs/IMPLEMENTATION_ENTRY_BRIEF.md`
- `docs/ARCHITECTURE_GUARDRAILS.md`

## Standalone Repo Rule

- Treat this repo as a standalone product.
- Do not compare it to sibling KProject repos or import cross-project ranking history unless explicitly asked.

## Product Rule

This repo is not allowed to start as a broad federal market-intelligence platform.

The required first wedge is:
- `federal_spec_decompiler`

That means:
- one agency cluster
- one requirement family
- one reusable primitive-extraction loop

## Data Rule

- Use real official sources only.
- Prefer APIs and official bulk docs over scraping.
- Never use synthetic solicitations or fake award history.

## First Workflow Rule

The first workflow must stay:
1. ingest narrow federal docs
2. extract repeatable kernels
3. show evidence
4. support a build / sell / incubate decision
