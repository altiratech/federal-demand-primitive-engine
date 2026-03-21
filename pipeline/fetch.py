from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.models import CorpusConfig, CorpusDocument, RawAttachment
from pipeline.sam import SamGovClient
from pipeline.text_utils import html_to_text, normalize_whitespace, slugify


FAMILY_LABELS = {
    "intake_routing": "intake / routing",
    "records_documentation": "records / documentation",
    "review_approval": "review / approval",
    "reporting_compliance_support": "reporting / compliance support",
}

CONTENT_TYPE_BY_SUFFIX = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".htm": "text/html",
    ".html": "text/html",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
}


def build_raw_corpus(
    config: CorpusConfig,
    client: SamGovClient,
    repo_root: Path,
) -> tuple[list[CorpusDocument], dict[str, Any]]:
    raw_root = repo_root / "data" / "raw" / config.corpus_id
    queries_root = raw_root / "queries"
    notices_root = raw_root / "notices"
    queries_root.mkdir(parents=True, exist_ok=True)
    notices_root.mkdir(parents=True, exist_ok=True)

    opportunities: dict[str, dict[str, Any]] = {}
    query_summaries: list[dict[str, Any]] = []
    requested_seed_notice_ids = list(config.seed_notice_ids)
    missing_seed_notice_ids: list[str] = []
    if requested_seed_notice_ids:
        for notice_id in requested_seed_notice_ids:
            query_file = queries_root / f"seed_{notice_id}.json"
            cached_payload = load_cached_json(query_file)
            if cached_payload is None:
                metadata = client.fetch_notice(notice_id)
                cached_payload = {
                    "totalRecords": 1 if metadata else 0,
                    "limit": 1,
                    "offset": 0,
                    "opportunitiesData": [metadata] if metadata else [],
                }
                query_file.write_text(json.dumps(cached_payload, indent=2, sort_keys=True))
            opportunities_data = cached_payload.get("opportunitiesData") or []
            metadata = opportunities_data[0] if opportunities_data else None
            query_summaries.append(
                {
                    "seed_notice_id": notice_id,
                    "retrieved_records": 1 if metadata else 0,
                    "cache_path": str(query_file),
                }
            )
            if metadata is None:
                missing_seed_notice_ids.append(notice_id)
                continue
            opportunities[notice_id] = metadata
    else:
        for window in config.date_windows:
            for procurement_type in config.procurement_types:
                offset = 0
                while True:
                    query_file = (
                        queries_root
                        / f"{window.posted_from.replace('/', '-')}_{window.posted_to.replace('/', '-')}_{procurement_type}_{offset}.json"
                    )
                    payload = load_cached_json(query_file)
                    if payload is None:
                        payload = client.search(
                            postedFrom=window.posted_from,
                            postedTo=window.posted_to,
                            organizationName=config.organization_name,
                            ptype=procurement_type,
                            limit=1000,
                            offset=offset,
                        )
                        query_file.write_text(json.dumps(payload, indent=2, sort_keys=True))
                    items = payload.get("opportunitiesData", [])
                    query_summaries.append(
                        {
                            "posted_from": window.posted_from,
                            "posted_to": window.posted_to,
                            "procurement_type": procurement_type,
                            "offset": offset,
                            "total_records": payload.get("totalRecords", 0),
                            "retrieved_records": len(items),
                            "cache_path": str(query_file),
                        }
                    )
                    for item in items:
                        opportunities.setdefault(item["noticeId"], item)
                    offset += len(items)
                    if not items or offset >= payload.get("totalRecords", 0):
                        break

    shortlisted_metadata: list[tuple[float, list[str], dict[str, Any], str]] = []
    for notice_id, metadata in opportunities.items():
        notice_root = notices_root / notice_id
        resource_links = metadata.get("resourceLinks") or []
        should_fetch_description = not resource_links
        description_path = notice_root / "description.json"
        description_payload = {"description": ""}
        if description_path.exists():
            description_payload = json.loads(description_path.read_text())
        if should_fetch_description and (
            not description_payload.get("description") or is_bad_description_payload(description_payload)
        ):
            try:
                description_payload = client.fetch_description(notice_id)
            except Exception as error:
                description_payload = {"description": "", "error": str(error)}
            notice_root.mkdir(parents=True, exist_ok=True)
            description_path.write_text(json.dumps(description_payload, indent=2, sort_keys=True))
        cached_description_text = ""
        if not is_bad_description_payload(description_payload):
            cached_description_text = html_to_text(description_payload.get("description") or "")
        selection_score, selection_matches = score_document(config, metadata, cached_description_text)
        if not resource_links:
            continue
        if selection_score < config.selection.minimum_score:
            continue
        shortlisted_metadata.append((selection_score, selection_matches, metadata, cached_description_text))

    selected_documents: list[CorpusDocument] = []
    for selection_score, selection_matches, metadata, cached_description_text in sorted(
        shortlisted_metadata,
        key=lambda item: (item[0], item[2].get("postedDate", ""), item[2]["noticeId"]),
        reverse=True,
    )[: config.selection.max_documents]:
        notice_id = metadata["noticeId"]
        notice_root = notices_root / notice_id
        notice_root.mkdir(parents=True, exist_ok=True)
        metadata_path = notice_root / "metadata.json"
        if not metadata_path.exists():
            metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True))

        description_html = ""
        description_text = cached_description_text
        description_path = notice_root / "description.json"
        if description_path.exists():
            description_payload = json.loads(description_path.read_text())
        else:
            description_payload = {"description": ""}
        resource_links = metadata.get("resourceLinks") or []
        should_fetch_description = not resource_links
        if should_fetch_description and (
            not description_payload.get("description") or is_bad_description_payload(description_payload)
        ):
            try:
                description_payload = client.fetch_description(notice_id)
            except Exception as error:
                description_payload = {"description": "", "error": str(error)}
            description_path.write_text(json.dumps(description_payload, indent=2, sort_keys=True))
        description_html = description_payload.get("description") or ""
        description_text = html_to_text(description_html)
        selected_documents.append(
            CorpusDocument(
                notice_id=notice_id,
                title=normalize_whitespace(metadata.get("title") or ""),
                solicitation_number=normalize_whitespace(metadata.get("solicitationNumber") or ""),
                posted_date=metadata.get("postedDate") or "",
                notice_type=metadata.get("type") or "",
                full_parent_path_name=metadata.get("fullParentPathName") or "",
                source_url=f"https://sam.gov/api/prod/opportunities/v1/noticedesc?noticeid={notice_id}",
                ui_link=metadata.get("uiLink"),
                resource_link_count=len(resource_links),
                description_html=description_html,
                description_text=description_text,
                selection_score=selection_score,
                selection_matches=selection_matches,
                raw_directory=str(notice_root),
            )
        )

    if config.attachment_policy.enabled:
        download_supported_attachments(config, client, repo_root, selected_documents)

    processed_root = repo_root / "data" / "processed" / config.corpus_id
    processed_root.mkdir(parents=True, exist_ok=True)
    selection_path = processed_root / "selected_documents.json"
    selection_path.write_text(
        json.dumps([document.to_dict() for document in selected_documents], indent=2, sort_keys=True)
    )

    corpus_summary = {
        "corpus_id": config.corpus_id,
        "label": config.label,
        "query_summaries": query_summaries,
        "total_unique_opportunities": len(opportunities),
        "selected_documents": len(selected_documents),
        "selection_threshold": config.selection.minimum_score,
        "seed_notice_ids": requested_seed_notice_ids,
        "missing_seed_notice_ids": missing_seed_notice_ids,
        "selection_path": str(selection_path),
    }
    return selected_documents, corpus_summary


def is_bad_description_payload(payload: dict[str, Any]) -> bool:
    if payload.get("description"):
        return False
    status = payload.get("status")
    if isinstance(status, int) and status >= 500:
        return True
    return bool(payload.get("error") or payload.get("errorCode") or payload.get("errorMessage"))


def load_cached_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def score_document(
    config: CorpusConfig,
    metadata: dict[str, Any],
    description_text: str,
) -> tuple[float, list[str]]:
    haystack = " ".join(
        [
            metadata.get("title") or "",
            metadata.get("solicitationNumber") or "",
            metadata.get("type") or "",
            description_text,
        ]
    ).lower()
    score = 0.0
    matches: list[str] = []

    for phrase, weight in config.selection.positive_keywords.items():
        if phrase in haystack:
            score += weight
            matches.append(f"+{phrase}")
    for phrase, weight in config.selection.negative_keywords.items():
        if phrase in haystack:
            score -= weight
            matches.append(f"-{phrase}")

    family_hits = 0
    for family_id, keywords in config.taxonomy_keywords.items():
        if any(keyword in haystack for keyword in keywords):
            score += 1.75
            matches.append(f"family:{family_id}")
            family_hits += 1

    if "information technology" in haystack or "software" in haystack or "system" in haystack:
        score += 1.5
        matches.append("+it-context")
    if metadata.get("resourceLinks"):
        score += 1.0
        matches.append("+attachments")
    if family_hits >= 2:
        score += 2.0
        matches.append("+multi-family")
    return score, matches


def download_supported_attachments(
    config: CorpusConfig,
    client: SamGovClient,
    repo_root: Path,
    documents: list[CorpusDocument],
) -> None:
    allowed = set(config.attachment_policy.allowed_content_types)
    attachment_document_count = 0
    for document in documents:
        if attachment_document_count >= config.attachment_policy.max_documents:
            break
        if document.selection_score < config.attachment_policy.min_selection_score:
            continue
        metadata = json.loads(Path(document.raw_directory, "metadata.json").read_text())
        urls = metadata.get("resourceLinks") or []
        if not urls:
            continue
        saved_attachments: list[RawAttachment] = []
        attachments_root = Path(document.raw_directory) / "attachments"
        attachments_root.mkdir(parents=True, exist_ok=True)
        manifest_path = attachments_root / "manifest.json"
        cached_manifest = load_attachment_manifest(manifest_path)
        for index, url in enumerate(urls[: config.attachment_policy.max_attachments_per_document], start=1):
            cached_attachment = cached_manifest.get(url)
            if cached_attachment is not None and Path(cached_attachment.raw_path).exists():
                saved_attachments.append(cached_attachment)
                continue
            reconstructed_attachment = reconstruct_cached_attachment(url, index, attachments_root, allowed)
            if reconstructed_attachment is not None:
                saved_attachments.append(reconstructed_attachment)
                continue
            try:
                filename, content_type = client.probe_attachment(url)
            except Exception:
                continue
            if content_type not in allowed:
                continue
            output_path = attachments_root / f"{index:02d}-{slugify(filename)}{Path(filename).suffix}"
            if not output_path.exists():
                client.download_attachment(url, output_path, config.attachment_policy.max_download_bytes)
            saved_attachments.append(
                RawAttachment(
                    source_url=url,
                    filename=filename,
                    content_type=content_type,
                    raw_path=str(output_path),
                )
            )
        if saved_attachments:
            document.attachments = saved_attachments
            write_attachment_manifest(manifest_path, saved_attachments)
            attachment_document_count += 1


def load_attachment_manifest(path: Path) -> dict[str, RawAttachment]:
    payload = load_cached_json(path)
    if payload is None:
        return {}
    attachments = payload.get("attachments")
    if not isinstance(attachments, list):
        return {}
    manifest: dict[str, RawAttachment] = {}
    for item in attachments:
        if not isinstance(item, dict):
            continue
        source_url = item.get("source_url")
        filename = item.get("filename")
        content_type = item.get("content_type")
        raw_path = item.get("raw_path")
        if not all(isinstance(value, str) and value for value in (source_url, filename, content_type, raw_path)):
            continue
        manifest[source_url] = RawAttachment(
            source_url=source_url,
            filename=filename,
            content_type=content_type,
            raw_path=raw_path,
        )
    return manifest


def write_attachment_manifest(path: Path, attachments: list[RawAttachment]) -> None:
    path.write_text(
        json.dumps(
            {"attachments": [attachment.to_dict() for attachment in attachments]},
            indent=2,
            sort_keys=True,
        )
    )


def reconstruct_cached_attachment(
    source_url: str,
    index: int,
    attachments_root: Path,
    allowed_content_types: set[str],
) -> RawAttachment | None:
    matches = sorted(attachments_root.glob(f"{index:02d}-*"))
    if not matches:
        return None
    output_path = matches[0]
    content_type = CONTENT_TYPE_BY_SUFFIX.get(output_path.suffix.lower())
    if content_type not in allowed_content_types:
        return None
    filename = output_path.name.split("-", 1)[-1]
    return RawAttachment(
        source_url=source_url,
        filename=filename,
        content_type=content_type,
        raw_path=str(output_path),
    )
