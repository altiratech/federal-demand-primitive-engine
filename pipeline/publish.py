from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.models import CorpusConfig, CorpusDocument, RequirementCandidate, RequirementKernel


def publish_kernel_artifact(
    config: CorpusConfig,
    repo_root: Path,
    *,
    corpus_summary: dict[str, object],
    documents: list[CorpusDocument],
    candidates: list[RequirementCandidate],
    kernels: list[RequirementKernel],
) -> dict[str, str]:
    output_root = repo_root / "artifacts" / config.corpus_id
    output_root.mkdir(parents=True, exist_ok=True)

    artifact_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus": {
            "corpus_id": config.corpus_id,
            "label": config.label,
            "organization_name": config.organization_name,
            "date_windows": [window.__dict__ for window in config.date_windows],
            "procurement_types": config.procurement_types,
            "selection_summary": corpus_summary,
        },
        "counts": {
            "documents": len(documents),
            "requirement_candidates": len(candidates),
            "kernels": len(kernels),
        },
        "kernels": [kernel.to_dict() for kernel in kernels],
    }

    json_path = output_root / "requirement_kernels.json"
    json_path.write_text(json.dumps(artifact_payload, indent=2, sort_keys=True))

    markdown_path = output_root / "requirement_kernels.md"
    markdown_path.write_text(render_markdown(config, documents, candidates, kernels))
    return {"json": str(json_path), "markdown": str(markdown_path)}


def render_markdown(
    config: CorpusConfig,
    documents: list[CorpusDocument],
    candidates: list[RequirementCandidate],
    kernels: list[RequirementKernel],
) -> str:
    lines = [
        f"# {config.label}",
        "",
        "## Corpus Summary",
        f"- documents selected: {len(documents)}",
        f"- requirement candidates: {len(candidates)}",
        f"- recurring kernels: {len(kernels)}",
        "",
        "## Kernel Library",
    ]
    for kernel in kernels:
        lines.extend(
            [
                "",
                f"### {kernel.label}",
                f"- family: {kernel.family_label}",
                f"- recurrence: {kernel.recurrence_count} snippets across {kernel.document_count} notices",
                f"- confidence: {kernel.confidence}",
                f"- representative requirement: {kernel.representative_requirement}",
                "- evidence:",
            ]
        )
        for evidence in kernel.evidence:
            lines.append(
                "  - "
                f"{evidence.posted_date} | {evidence.title} | {evidence.section_title} | "
                f"{evidence.snippet_text}"
            )
    return "\n".join(lines) + "\n"
