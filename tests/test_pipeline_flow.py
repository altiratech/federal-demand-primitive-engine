from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from pipeline.cluster import cluster_requirement_candidates, generate_kernel_label
from pipeline.config import load_corpus_config
from pipeline.extract import extract_requirement_candidates, is_excluded_requirement
from pipeline.models import CorpusDocument
from pipeline.normalize import build_sections, description_sections
from pipeline.publish import publish_kernel_artifact
from pipeline.text_utils import clean_ocr_text


def make_config():
    config = load_corpus_config(Path("configs/va_case_management_workflow_support_v1.json"))
    return replace(
        config,
        clustering=replace(config.clustering, min_cluster_evidence=2, max_kernels=4),
    )


def make_document(
    *,
    notice_id: str,
    title: str,
    posted_date: str,
    description_html: str,
) -> CorpusDocument:
    return CorpusDocument(
        notice_id=notice_id,
        title=title,
        solicitation_number=f"SOL-{notice_id}",
        posted_date=posted_date,
        notice_type="Sources Sought",
        full_parent_path_name="VETERANS AFFAIRS",
        source_url=f"https://sam.gov/api/prod/opportunities/v1/noticedesc?noticeid={notice_id}",
        ui_link=f"https://sam.gov/opp/{notice_id}/view",
        resource_link_count=1,
        description_html=description_html,
        description_text="",
        selection_score=10.0,
        selection_matches=["+case management"],
        raw_directory=f"/tmp/{notice_id}",
    )


def test_description_sections_parser_handles_headings_and_tables() -> None:
    document = make_document(
        notice_id="notice-parser",
        title="Parser Test",
        posted_date="2025-02-01",
        description_html="""
        <h2>Workflow Requirements</h2>
        <p>The contractor shall route referrals and document intake updates.</p>
        <table>
          <tr><th>Artifact</th><th>Action</th></tr>
          <tr><td>Referral</td><td>Track</td></tr>
        </table>
        <h2>Reporting</h2>
        <p>The contractor shall provide dashboard reporting for compliance reviews.</p>
        """,
    )

    sections = description_sections(document)

    assert len(sections) == 2
    assert sections[0].section_title == "Workflow Requirements"
    assert "Artifact | Action ; Referral | Track" in sections[0].section_text
    assert sections[1].section_title == "Reporting"
    assert sections[1].family_hint == "reporting / compliance support"


def test_extract_requirement_candidates_preserves_schema(tmp_path: Path) -> None:
    config = make_config()
    document = make_document(
        notice_id="notice-extract",
        title="Extraction Test",
        posted_date="2025-02-02",
        description_html="""
        <p>The contractor shall route referrals, track intake status, and document decisions for each Veteran case.</p>
        <p>The contractor shall route referrals, track intake status, and document decisions for each Veteran case.</p>
        """,
    )

    sections = description_sections(document)
    candidates = extract_requirement_candidates(config, tmp_path, sections)

    assert len(candidates) == 1
    payload = candidates[0].to_dict()
    assert payload["family_id"] == "intake_routing"
    assert payload["family_label"] == "intake / routing"
    assert payload["cleaned_text"] == payload["raw_text"]
    assert payload["normalized_text"]
    assert {"candidate_id", "notice_id", "raw_text", "cleaned_text", "normalized_text", "source_url"} <= set(payload)


def test_clean_ocr_text_repairs_common_spacing_and_character_noise() -> None:
    assert clean_ocr_text("High-CostMedication: When prior authorization is required for a Veterans stay.") == (
        "High-Cost Medication: When prior authorization is required for a Veteran's stay."
    )
    assert clean_ocr_text("Selected VAstaff will be providedaccess to the CNH electronic health record.") == (
        "Selected VA staff will be provided access to the CNH electronic health record."
    )


def test_is_excluded_requirement_filters_contract_admin_noise() -> None:
    assert is_excluded_requirement("Claims must be submitted to the VA facility that issued the authorization.")
    assert is_excluded_requirement(
        "After reviewing SAM information, the Offeror verifies by submission of this offer that the representations and certifications currently posted electronically at FAR 52.212-3 are current."
    )
    assert is_excluded_requirement(
        "The Contractor shall comply with the provisions of this paragraph if this contract was awarded using other than sealed bid and is in excess of the simplified acquisition threshold."
    )
    assert not is_excluded_requirement(
        "Reporting shall include date of occurrence and patient disposition and outcome."
    )


def test_generate_kernel_label_prefers_domain_specific_phrases() -> None:
    assert (
        generate_kernel_label(
            "All medical records concerning the Veteran's care in the CNH shall be readily accessible to VA.",
            ["all medical records concerning the veteran care in the cnh shall be readily accessible to agency"],
        )
        == "Medical Records Accessible To VA"
    )
    assert (
        generate_kernel_label(
            "Changes in the status of the licensure will be immediately reported to the Department of Veterans Affairs.",
            ["changes in the status of the licensure will be immediately reported to the agency"],
        )
        == "Report Licensure Status Changes"
    )


def test_cluster_requirement_candidates_smoke(tmp_path: Path) -> None:
    config = make_config()
    documents = [
        make_document(
            notice_id="notice-one",
            title="Workflow One",
            posted_date="2025-01-10",
            description_html="<p>The contractor shall route referrals, track intake status, and document decisions for each Veteran case.</p>",
        ),
        make_document(
            notice_id="notice-two",
            title="Workflow Two",
            posted_date="2025-01-12",
            description_html="<p>The contractor shall support referral routing, intake tracking, and case documentation updates.</p>",
        ),
    ]

    sections = []
    for document in documents:
        sections.extend(description_sections(document))
    candidates = extract_requirement_candidates(config, tmp_path, sections)
    kernels = cluster_requirement_candidates(
        candidates,
        similarity_threshold=0.35,
        min_cluster_evidence=2,
        max_kernels=4,
    )

    assert len(kernels) == 1
    assert kernels[0].family_id == "intake_routing"
    assert kernels[0].document_count == 2
    assert kernels[0].recurrence_count >= 2
    assert len(kernels[0].evidence) == 2


def test_corpus_to_kernel_integration(tmp_path: Path) -> None:
    config = make_config()
    repo_root = tmp_path
    documents = [
        make_document(
            notice_id="notice-int-1",
            title="VA Workflow Support",
            posted_date="2025-01-05",
            description_html="<h2>Requirements</h2><p>The contractor shall route referrals, track intake status, and document decisions for each Veteran case.</p>",
        ),
        make_document(
            notice_id="notice-int-2",
            title="VA Case Coordination Support",
            posted_date="2025-01-06",
            description_html="<h2>Requirements</h2><p>The contractor shall route referrals, maintain intake workflows, and document case decisions for care coordination.</p>",
        ),
    ]

    sections = build_sections(config, repo_root, documents)
    candidates = extract_requirement_candidates(config, repo_root, sections)
    kernels = cluster_requirement_candidates(
        candidates,
        similarity_threshold=0.35,
        min_cluster_evidence=2,
        max_kernels=4,
    )
    artifact_paths = publish_kernel_artifact(
        config,
        repo_root,
        corpus_summary={"selected_documents": len(documents)},
        documents=documents,
        candidates=candidates,
        kernels=kernels,
    )

    assert len(sections) == 2
    assert len(candidates) == 2
    assert len(kernels) == 1

    artifact_payload = json.loads(Path(artifact_paths["json"]).read_text())
    assert artifact_payload["counts"]["kernels"] == 1
    assert artifact_payload["kernels"][0]["document_count"] == 2
    assert "representative raw evidence" in Path(artifact_paths["markdown"]).read_text()
    assert "analyst snippet:" in Path(artifact_paths["markdown"]).read_text()
