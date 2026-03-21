from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class DateWindow:
    posted_from: str
    posted_to: str


@dataclass(frozen=True)
class SelectionSettings:
    max_documents: int
    minimum_score: float
    minimum_description_chars: int
    positive_keywords: dict[str, float]
    negative_keywords: dict[str, float]


@dataclass(frozen=True)
class AttachmentPolicy:
    enabled: bool
    max_documents: int
    max_attachments_per_document: int
    min_selection_score: float
    max_download_bytes: int
    allowed_content_types: list[str]


@dataclass(frozen=True)
class ClusteringSettings:
    similarity_threshold: float
    min_cluster_evidence: int
    max_kernels: int


@dataclass(frozen=True)
class CorpusConfig:
    corpus_id: str
    label: str
    organization_name: str
    seed_notice_ids: list[str]
    date_windows: list[DateWindow]
    procurement_types: list[str]
    api: dict[str, str]
    selection: SelectionSettings
    attachment_policy: AttachmentPolicy
    taxonomy_keywords: dict[str, list[str]]
    requirement_verbs: list[str]
    clustering: ClusteringSettings


@dataclass
class RawAttachment:
    source_url: str
    filename: str
    content_type: str
    raw_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CorpusDocument:
    notice_id: str
    title: str
    solicitation_number: str
    posted_date: str
    notice_type: str
    full_parent_path_name: str
    source_url: str
    ui_link: str | None
    resource_link_count: int
    description_html: str
    description_text: str
    selection_score: float
    selection_matches: list[str]
    raw_directory: str
    attachments: list[RawAttachment] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["attachments"] = [attachment.to_dict() for attachment in self.attachments]
        return payload


@dataclass
class DocumentSection:
    section_id: str
    notice_id: str
    title: str
    posted_date: str
    family_hint: str | None
    source_part: str
    section_key: str
    section_title: str
    section_text: str
    source_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RequirementCandidate:
    candidate_id: str
    notice_id: str
    title: str
    posted_date: str
    family_id: str
    family_label: str
    source_part: str
    section_id: str
    section_title: str
    raw_text: str
    cleaned_text: str
    normalized_text: str
    tokens: list[str]
    requirement_score: float
    source_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KernelEvidence:
    notice_id: str
    title: str
    posted_date: str
    section_title: str
    source_part: str
    cleaned_snippet_text: str
    raw_snippet_text: str
    source_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RequirementKernel:
    kernel_id: str
    label: str
    family_id: str
    family_label: str
    recurrence_count: int
    document_count: int
    representative_requirement: str
    representative_requirement_raw: str
    confidence: float
    top_terms: list[str]
    evidence: list[KernelEvidence]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        return payload
