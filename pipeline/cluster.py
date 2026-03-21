from __future__ import annotations

from collections import Counter

from pipeline.models import KernelEvidence, RequirementCandidate, RequirementKernel
from pipeline.text_utils import counter_cosine_similarity, phrase_counts, stable_hash, title_case_phrase


def cluster_requirement_candidates(
    candidates: list[RequirementCandidate],
    *,
    similarity_threshold: float,
    min_cluster_evidence: int,
    max_kernels: int,
) -> list[RequirementKernel]:
    clusters: list[dict[str, object]] = []
    for candidate in sorted(candidates, key=lambda item: (item.family_id, item.requirement_score), reverse=True):
        candidate_counter = Counter(candidate.tokens)
        best_cluster: dict[str, object] | None = None
        best_score = 0.0
        for cluster in clusters:
            if cluster["family_id"] != candidate.family_id:
                continue
            score = counter_cosine_similarity(cluster["token_counter"], candidate_counter)
            if score > best_score:
                best_score = score
                best_cluster = cluster
        if best_cluster is None or best_score < similarity_threshold:
            clusters.append(
                {
                    "family_id": candidate.family_id,
                    "family_label": candidate.family_label,
                    "token_counter": candidate_counter,
                    "texts": [candidate.normalized_text],
                    "evidence": [candidate],
                    "documents": {candidate.notice_id},
                    "representative": candidate,
                }
            )
            continue
        best_cluster["token_counter"].update(candidate_counter)
        best_cluster["texts"].append(candidate.normalized_text)
        best_cluster["evidence"].append(candidate)
        best_cluster["documents"].add(candidate.notice_id)
        representative = best_cluster["representative"]
        if candidate.requirement_score > representative.requirement_score:
            best_cluster["representative"] = candidate

    kernels: list[RequirementKernel] = []
    for cluster in clusters:
        evidence_items = cluster["evidence"]
        if len(evidence_items) < min_cluster_evidence:
            continue
        representative = cluster["representative"]
        texts = cluster["texts"]
        phrase = best_phrase(texts) or default_phrase(cluster["family_label"])
        top_terms = [term for term, _ in cluster["token_counter"].most_common(6)]
        recurrence_count = len(evidence_items)
        document_count = len(cluster["documents"])
        confidence = min(0.96, 0.35 + (0.06 * recurrence_count) + (0.04 * document_count))
        evidence = [
            KernelEvidence(
                notice_id=item.notice_id,
                title=item.title,
                posted_date=item.posted_date,
                section_title=item.section_title,
                source_part=item.source_part,
                snippet_text=item.raw_text,
                source_url=item.source_url,
            )
            for item in dedupe_evidence(evidence_items)[:4]
        ]
        kernels.append(
            RequirementKernel(
                kernel_id=stable_hash(f"{cluster['family_id']}:{phrase}"),
                label=phrase,
                family_id=cluster["family_id"],
                family_label=cluster["family_label"],
                recurrence_count=recurrence_count,
                document_count=document_count,
                representative_requirement=representative.raw_text,
                confidence=round(confidence, 2),
                top_terms=top_terms,
                evidence=evidence,
            )
        )

    return sorted(
        kernels,
        key=lambda item: (item.document_count, item.recurrence_count, item.confidence),
        reverse=True,
    )[:max_kernels]


def best_phrase(texts: list[str]) -> str | None:
    phrase_counter = phrase_counts(texts, size=2)
    if not phrase_counter:
        phrase_counter = phrase_counts(texts, size=1)
    if not phrase_counter:
        return None
    phrase, _ = phrase_counter.most_common(1)[0]
    return title_case_phrase(phrase)


def default_phrase(family_label: str) -> str:
    mapping = {
        "intake / routing": "Intake And Routing Support",
        "records / documentation": "Documentation And Record Updates",
        "review / approval": "Review And Approval Workflow",
        "reporting / compliance support": "Reporting And Compliance Support",
    }
    return mapping[family_label]


def dedupe_evidence(items: list[RequirementCandidate]) -> list[RequirementCandidate]:
    seen: set[str] = set()
    output: list[RequirementCandidate] = []
    for item in sorted(items, key=lambda candidate: candidate.requirement_score, reverse=True):
        if item.notice_id in seen:
            continue
        seen.add(item.notice_id)
        output.append(item)
    return output
