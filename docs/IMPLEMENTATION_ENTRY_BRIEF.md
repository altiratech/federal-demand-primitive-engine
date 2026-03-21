# Federal Demand Primitive Engine Implementation Entry Brief

Purpose: keep the first engineering passes focused on the `federal_spec_decompiler` wedge.

## Current Product Center

Build the smallest serious loop:

1. ingest a narrow solicitation corpus
2. normalize source text
3. extract recurring requirement kernels
4. cluster and label them
5. show evidence-backed primitives the user can inspect

## First Build Blocks

### 1. Data model foundation

Lock schemas for:
- documents
- document sections
- requirement kernels
- evidence snippets
- cluster labels

### 2. Core APIs or payloads

Initial product access should support:
- corpus search
- kernel list
- kernel detail
- source evidence inspection

### 3. Web surfaces

Initial web surfaces should support:
- kernel explorer
- evidence panel
- taxonomy or cluster view

## Explicit Defers

Do not treat these as founding blockers:
- broad agency coverage
- pre-RFP prediction
- award analytics
- whitespace map

## Design Guardrail

This product should feel like a serious requirement-intelligence workbench, not a generic federal market map.
