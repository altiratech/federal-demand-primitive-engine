from __future__ import annotations

import re
from collections import Counter

from pipeline.models import KernelEvidence, RequirementCandidate, RequirementKernel
from pipeline.text_utils import counter_cosine_similarity, phrase_counts, stable_hash, title_case_phrase


LABEL_PATTERNS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("prior authorization", "therapy", "medication"), "Prior Authorization For Non-Routine Services"),
    (("prior authorization", "escort"), "Prior Authorization For Escort Services"),
    (("prior authorization", "therapy"), "Prior Authorization For Therapy Services"),
    (("prior authorization", "pt"), "Prior Authorization For Therapy Services"),
    (("prior authorization", "ot"), "Prior Authorization For Therapy Services"),
    (("prior authorization", "slp"), "Prior Authorization For Therapy Services"),
    (("prior authorization", "medication"), "Prior Authorization For High-Cost Medications"),
    (("medical records", "accessible to va"), "Medical Records Accessible To VA"),
    (("electronic health record",), "VA Access To Facility EHR"),
    (("licensure", "reported"), "Report Licensure Status Changes"),
    (("licensure", "report"), "Report Licensure Status Changes"),
    (("date of occurrence", "patient disposition"), "Incident Reporting With Outcome Details"),
    (("primary medical care", "preauthorized by va"), "Provide Preauthorized Clinical Support Services"),
    (("provider visits", "preauthorized by va"), "Provide Preauthorized Clinical Support Services"),
    (("approved referral for medical care",), "Use VA Referral Authorization Form"),
)

LABEL_STOPWORDS = {
    "agency",
    "any",
    "authorized",
    "care",
    "cnh",
    "cnhs",
    "contract",
    "contractor",
    "each",
    "facility",
    "medical",
    "other",
    "patient",
    "patients",
    "primary",
    "provider",
    "providers",
    "services",
    "shall",
    "staff",
    "that",
    "the",
    "this",
    "those",
    "veteran",
    "veterans",
    "will",
}

ACRONYM_MAP = {
    "cnh": "CNH",
    "cnhs": "CNHs",
    "ehr": "EHR",
    "ot": "OT",
    "pt": "PT",
    "slp": "SLP",
    "va": "VA",
}


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
                }
            )
            continue
        best_cluster["token_counter"].update(candidate_counter)
        best_cluster["texts"].append(candidate.normalized_text)
        best_cluster["evidence"].append(candidate)
        best_cluster["documents"].add(candidate.notice_id)

    kernels: list[RequirementKernel] = []
    for cluster in clusters:
        evidence_items = cluster["evidence"]
        if len(evidence_items) < min_cluster_evidence:
            continue
        document_count = len(cluster["documents"])
        if document_count < 2:
            continue
        representative = choose_representative(evidence_items)
        texts = cluster["texts"]
        phrase = generate_kernel_label(representative.raw_text, texts) or best_phrase(texts) or default_phrase(
            cluster["family_label"]
        )
        top_terms = [term for term, _ in cluster["token_counter"].most_common(6)]
        recurrence_count = len(evidence_items)
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


def generate_kernel_label(representative_text: str, cluster_texts: list[str]) -> str | None:
    samples = " || ".join([representative_text.lower(), *cluster_texts[:3]])
    for required_terms, label in LABEL_PATTERNS:
        if all(term in samples for term in required_terms):
            return label
    return fallback_label(representative_text)


def fallback_label(text: str) -> str | None:
    cleaned = normalize_label_source(text)
    if not cleaned:
        return None
    words = [
        format_label_word(word)
        for word in re.findall(r"[a-zA-Z0-9]+", cleaned)
        if len(word) > 2 and word.lower() not in LABEL_STOPWORDS
    ]
    deduped_words: list[str] = []
    for word in words:
        if word in deduped_words:
            continue
        deduped_words.append(word)
    if not deduped_words:
        return None
    return " ".join(deduped_words[:5])


def normalize_label_source(text: str) -> str:
    lowered = text.lower().strip()
    lowered = lowered.lstrip("•- ")
    lowered = re.sub(r"^\(?[a-z0-9]+\)?[.)-]?\s*", "", lowered)
    lowered = re.sub(
        r"^(the\s+)?(contractor|provider|providers|cnh|cnhs|selected va staff|duly authorized va staff|va staff)\s+(shall|will|must)\s+",
        "",
        lowered,
    )
    lowered = re.sub(r"^(all medical records.*?)\s+(shall|will|must)\s+be\s+", r"\1 ", lowered)
    lowered = lowered.split(":", 1)[-1]
    lowered = re.split(r"[.;]", lowered, maxsplit=1)[0]
    lowered = re.split(r",\s+(?:and|including|without)\b", lowered, maxsplit=1)[0]
    return lowered.strip()


def format_label_word(word: str) -> str:
    lowered = word.lower()
    if lowered in ACRONYM_MAP:
        return ACRONYM_MAP[lowered]
    return lowered.capitalize()


def choose_representative(items: list[RequirementCandidate]) -> RequirementCandidate:
    return max(
        items,
        key=lambda item: (
            representative_quality_score(item),
            item.requirement_score,
        ),
    )


def representative_quality_score(item: RequirementCandidate) -> float:
    lowered = item.raw_text.lower()
    noise_penalty = 0.0
    for phrase in (
        "page ",
        "request for information",
        "payment amount",
        "contracting officer",
        "privacy act of 1974",
    ):
        if phrase in lowered:
            noise_penalty += 0.6
    if item.raw_text.lstrip()[:1].isdigit():
        noise_penalty += 0.8
    length_penalty = max(0.0, len(item.raw_text) - 120) * 0.01
    return item.requirement_score - noise_penalty - length_penalty
