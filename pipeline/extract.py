from __future__ import annotations

import json
from pathlib import Path

from pipeline.fetch import FAMILY_LABELS
from pipeline.models import CorpusConfig, DocumentSection, RequirementCandidate
from pipeline.text_utils import canonicalize_requirement, sentence_split, stable_hash, tokenize


EXCLUDED_REQUIREMENT_PHRASES = (
    "system for award management",
    "covered telecommunications equipment or services",
    "submission of its offer",
    "offeror represents",
    "internal confidentiality agreements",
    "lawfully reporting waste, fraud, or abuse",
    "service contract reporting requirements",
    "tax court review",
    "federal awards",
)


def extract_requirement_candidates(
    config: CorpusConfig,
    repo_root: Path,
    sections: list[DocumentSection],
) -> list[RequirementCandidate]:
    candidates: list[RequirementCandidate] = []
    seen_keys: set[tuple[str, str]] = set()
    requirement_verbs = set(config.requirement_verbs)
    for section in sections:
        for sentence in sentence_split(section.section_text):
            if is_excluded_requirement(sentence):
                continue
            tokens = tokenize(sentence)
            if len(tokens) < 6:
                continue
            family_id, family_score = assign_family(config, sentence)
            verb_score = sum(1.0 for verb in requirement_verbs if verb in sentence.lower())
            imperative_bonus = 1.5 if sentence.lower().startswith(("contractor shall", "shall ", "must ")) else 0.0
            requirement_score = family_score + verb_score + imperative_bonus
            if not family_id or requirement_score < 2.75:
                continue
            normalized_text = canonicalize_requirement(sentence)
            dedupe_key = (section.notice_id, normalized_text)
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            candidates.append(
                RequirementCandidate(
                    candidate_id=stable_hash(f"{section.section_id}:{normalized_text}"),
                    notice_id=section.notice_id,
                    title=section.title,
                    posted_date=section.posted_date,
                    family_id=family_id,
                    family_label=FAMILY_LABELS[family_id],
                    source_part=section.source_part,
                    section_id=section.section_id,
                    section_title=section.section_title,
                    raw_text=sentence,
                    normalized_text=normalized_text,
                    tokens=tokenize(normalized_text),
                    requirement_score=requirement_score,
                    source_url=section.source_url,
                )
            )

    output_root = repo_root / "data" / "processed" / config.corpus_id
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / "requirement_candidates.jsonl"
    with output_path.open("w") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate.to_dict(), sort_keys=True) + "\n")
    return candidates


def assign_family(config: CorpusConfig, sentence: str) -> tuple[str | None, float]:
    lowered = sentence.lower()
    best_family: str | None = None
    best_score = 0.0
    for family_id, keywords in config.taxonomy_keywords.items():
        score = sum(1.0 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_family = family_id
            best_score = score
    return best_family, best_score


def is_excluded_requirement(sentence: str) -> bool:
    lowered = sentence.lower()
    if any(phrase in lowered for phrase in EXCLUDED_REQUIREMENT_PHRASES):
        return True
    if lowered.startswith("[]") or "[reserved]" in lowered or "52.204" in lowered:
        return True
    return False
