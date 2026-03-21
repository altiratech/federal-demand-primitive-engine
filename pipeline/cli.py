from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.cluster import cluster_requirement_candidates
from pipeline.config import DEFAULT_CONFIG_PATH, load_corpus_config
from pipeline.extract import extract_requirement_candidates
from pipeline.fetch import build_raw_corpus
from pipeline.normalize import build_sections
from pipeline.publish import publish_kernel_artifact
from pipeline.sam import SamGovClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the first federal demand primitive slice.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the locked corpus config JSON.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    config = load_corpus_config(args.config)
    client = SamGovClient(
        search_url=config.api["search_url"],
        description_url_template=config.api["description_url_template"],
        public_key_discovery_url=config.api["public_key_discovery_url"],
    )

    documents, corpus_summary = build_raw_corpus(config, client, repo_root)
    sections = build_sections(config, repo_root, documents)
    candidates = extract_requirement_candidates(config, repo_root, sections)
    kernels = cluster_requirement_candidates(
        candidates,
        similarity_threshold=config.clustering.similarity_threshold,
        min_cluster_evidence=config.clustering.min_cluster_evidence,
        max_kernels=config.clustering.max_kernels,
    )
    artifact_paths = publish_kernel_artifact(
        config,
        repo_root,
        corpus_summary=corpus_summary,
        documents=documents,
        candidates=candidates,
        kernels=kernels,
    )

    print(f"Selected documents: {len(documents)}")
    print(f"Normalized sections: {len(sections)}")
    print(f"Requirement candidates: {len(candidates)}")
    print(f"Kernels: {len(kernels)}")
    print(f"Artifact JSON: {artifact_paths['json']}")
    print(f"Artifact Markdown: {artifact_paths['markdown']}")


if __name__ == "__main__":
    main()
