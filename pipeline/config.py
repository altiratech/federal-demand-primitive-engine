from __future__ import annotations

import json
from pathlib import Path

from pipeline.models import (
    AttachmentPolicy,
    ClusteringSettings,
    CorpusConfig,
    DateWindow,
    SelectionSettings,
)


DEFAULT_CONFIG_PATH = Path("configs/va_case_management_workflow_support_v1.json")


def load_corpus_config(path: Path | None = None) -> CorpusConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    payload = json.loads(config_path.read_text())
    return CorpusConfig(
        corpus_id=payload["corpus_id"],
        label=payload["label"],
        organization_name=payload["organization_name"],
        seed_notice_ids=list(payload.get("seed_notice_ids", [])),
        date_windows=[DateWindow(**item) for item in payload["date_windows"]],
        procurement_types=list(payload["procurement_types"]),
        api=dict(payload["api"]),
        selection=SelectionSettings(**payload["selection"]),
        attachment_policy=AttachmentPolicy(**payload["attachment_policy"]),
        taxonomy_keywords={key: list(values) for key, values in payload["taxonomy_keywords"].items()},
        requirement_verbs=list(payload["requirement_verbs"]),
        clustering=ClusteringSettings(**payload["clustering"]),
    )
