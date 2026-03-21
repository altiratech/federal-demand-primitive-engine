from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from pipeline.config import load_corpus_config
from pipeline.fetch import build_raw_corpus


class FakeSamClient:
    def __init__(self) -> None:
        self.notice_calls: list[str] = []
        self.description_calls: list[str] = []
        self.probe_calls: list[str] = []
        self.download_calls: list[str] = []
        self._metadata = {
            "notice-alpha": {
                "noticeId": "notice-alpha",
                "title": "VA Case Management Workflow Support",
                "solicitationNumber": "36C10B25Q0001",
                "postedDate": "2025-03-01",
                "type": "Sources Sought",
                "fullParentPathName": "VETERANS AFFAIRS",
                "resourceLinks": ["https://sam.gov/files/alpha.pdf"],
                "uiLink": "https://sam.gov/opp/notice-alpha/view",
            },
            "notice-beta": {
                "noticeId": "notice-beta",
                "title": "VA Intake Routing and Dashboard Support Services",
                "solicitationNumber": "36C10B25Q0002",
                "postedDate": "2025-03-03",
                "type": "Combined Synopsis/Solicitation",
                "fullParentPathName": "VETERANS AFFAIRS",
                "resourceLinks": ["https://sam.gov/files/beta.pdf"],
                "uiLink": "https://sam.gov/opp/notice-beta/view",
            },
        }

    def fetch_notice(self, notice_id: str) -> dict[str, object] | None:
        self.notice_calls.append(notice_id)
        return self._metadata.get(notice_id)

    def fetch_description(self, notice_id: str) -> dict[str, str]:
        self.description_calls.append(notice_id)
        return {
            "description": (
                "<h2>Workflow</h2><p>The contractor shall route referrals, "
                "track intake status, and document case updates for Veterans Affairs.</p>"
            )
        }

    def probe_attachment(self, url: str) -> tuple[str, str]:
        self.probe_calls.append(url)
        return ("workflow-support.pdf", "application/pdf")

    def download_attachment(self, url: str, output_path: Path, max_bytes: int) -> None:
        self.download_calls.append(f"{url}:{max_bytes}")
        output_path.write_text("PDF placeholder")


class CacheOnlySamClient:
    def fetch_notice(self, notice_id: str) -> dict[str, object] | None:
        raise AssertionError(f"seed notice {notice_id} should have been loaded from cache")

    def fetch_description(self, notice_id: str) -> dict[str, str]:
        raise AssertionError(f"description {notice_id} should have been loaded from cache")

    def probe_attachment(self, url: str) -> tuple[str, str]:
        raise AssertionError(f"attachment probe {url} should have been loaded from cache")

    def download_attachment(self, url: str, output_path: Path, max_bytes: int) -> None:
        raise AssertionError(f"attachment download {url} should have been loaded from cache")


def make_config():
    config = load_corpus_config(Path("configs/va_case_management_workflow_support_v1.json"))
    return replace(
        config,
        seed_notice_ids=["notice-alpha", "notice-beta", "notice-missing"],
        selection=replace(config.selection, max_documents=5, minimum_score=4.0),
        attachment_policy=replace(config.attachment_policy, enabled=False),
    )


def test_build_raw_corpus_uses_locked_seed_cache(tmp_path: Path) -> None:
    repo_root = tmp_path
    config = make_config()

    first_client = FakeSamClient()
    documents, summary = build_raw_corpus(config, first_client, repo_root)

    assert [document.notice_id for document in documents] == ["notice-beta", "notice-alpha"]
    assert summary["missing_seed_notice_ids"] == ["notice-missing"]
    assert first_client.notice_calls == ["notice-alpha", "notice-beta", "notice-missing"]
    assert first_client.description_calls == []
    assert (repo_root / "data" / "raw" / config.corpus_id / "queries" / "seed_notice-alpha.json").exists()
    assert (repo_root / "data" / "raw" / config.corpus_id / "notices" / "notice-alpha" / "metadata.json").exists()
    assert not (repo_root / "data" / "raw" / config.corpus_id / "notices" / "notice-alpha" / "description.json").exists()
    assert (repo_root / "data" / "processed" / config.corpus_id / "selected_documents.json").exists()

    second_client = CacheOnlySamClient()
    cached_documents, cached_summary = build_raw_corpus(config, second_client, repo_root)

    assert [document.notice_id for document in cached_documents] == ["notice-beta", "notice-alpha"]
    assert cached_summary["missing_seed_notice_ids"] == ["notice-missing"]


def test_build_raw_corpus_reuses_cached_attachment_manifest(tmp_path: Path) -> None:
    repo_root = tmp_path
    base_config = make_config()
    config = replace(
        base_config,
        seed_notice_ids=["notice-alpha"],
        selection=replace(base_config.selection, max_documents=1, minimum_score=0.0),
        attachment_policy=replace(
            base_config.attachment_policy,
            enabled=True,
            max_documents=1,
            max_attachments_per_document=1,
            min_selection_score=0.0,
            allowed_content_types=["application/pdf"],
        ),
    )

    first_client = FakeSamClient()
    first_documents, _ = build_raw_corpus(config, first_client, repo_root)

    assert len(first_documents) == 1
    assert len(first_documents[0].attachments) == 1
    assert first_client.probe_calls == ["https://sam.gov/files/alpha.pdf"]
    assert len(first_client.download_calls) == 1
    manifest_path = (
        repo_root
        / "data"
        / "raw"
        / config.corpus_id
        / "notices"
        / "notice-alpha"
        / "attachments"
        / "manifest.json"
    )
    assert manifest_path.exists()

    second_client = CacheOnlySamClient()
    cached_documents, _ = build_raw_corpus(config, second_client, repo_root)

    assert len(cached_documents) == 1
    assert len(cached_documents[0].attachments) == 1
    assert cached_documents[0].attachments[0].content_type == "application/pdf"
    selected_documents = json.loads(
        (repo_root / "data" / "processed" / config.corpus_id / "selected_documents.json").read_text()
    )
    assert len(selected_documents[0]["attachments"]) == 1
