# Federal Demand Primitive Engine Architecture Guardrails

## Scope Guardrails

- Start with the decompiler wedge only.
- One corpus before many corpora.
- Evidence before taxonomy ambition.

## Data Guardrails

- Core objects:
  - `document`
  - `section`
  - `requirement_kernel`
  - `evidence`
  - `cluster`
- Keep raw text, normalized text, and inferred kernels separate.
- Synthetic data is prohibited.

## Product Guardrails

- user should see reusable primitives, not just summarized documents
- source evidence must stay inspectable
- UI should emphasize kernels and evidence, not generic dashboard chrome

## Repo Guardrails

- Keep the repo standalone.
- Do not design for full federal sprawl in v1.
- Prefer a narrow, inspectable build loop.
