from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


class SamGovClient:
    def __init__(
        self,
        *,
        search_url: str,
        description_url_template: str,
        public_key_discovery_url: str,
        api_key: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.search_url = search_url
        self.description_url_template = description_url_template
        self.public_key_discovery_url = public_key_discovery_url
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key or os.getenv("SAM_API_KEY") or self.discover_public_api_key()

    def discover_public_api_key(self) -> str:
        html = self._curl_text(self.public_key_discovery_url)
        match = re.search(r'"API_UMBRELLA_KEY":"([^"]+)"', html)
        if not match:
            raise RuntimeError("Could not discover the public SAM.gov API key.")
        return match.group(1)

    def search(self, **params: Any) -> dict[str, Any]:
        payload = dict(params)
        payload["api_key"] = self.api_key
        return self._request_json(self.search_url, payload)

    def fetch_notice(self, notice_id: str) -> dict[str, Any] | None:
        payload = self.search(noticeid=notice_id)
        opportunities = payload.get("opportunitiesData") or []
        if not opportunities:
            return None
        return opportunities[0]

    def fetch_description(self, notice_id: str) -> dict[str, Any]:
        url = self.description_url_template.format(notice_id=notice_id)
        return self._request_json(url, {"api_key": self.api_key})

    def probe_attachment(self, url: str) -> tuple[str, str]:
        headers_text = self._curl_headers(url)
        header_map = parse_headers(headers_text)
        content_type = header_map.get("content-type", "application/octet-stream").split(";")[0].strip()
        filename = extract_filename(header_map, url)
        return filename, content_type

    def download_attachment(self, url: str, destination: Path, max_download_bytes: int) -> None:
        data = self._curl_bytes(url, follow_redirects=True)
        if len(data) > max_download_bytes:
            raise ValueError(f"Attachment exceeded limit of {max_download_bytes} bytes: {url}")
        destination.write_bytes(data)

    def _request_json(self, base_url: str, params: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        query = urlencode({key: value for key, value in params.items() if value is not None})
        url = f"{base_url}?{query}"
        for attempt in range(3):
            try:
                payload = json.loads(self._curl_text(url))
                if is_retryable_payload(payload):
                    raise RuntimeError(f"Retryable SAM payload for {base_url}: {payload}")
                return payload
            except (RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
                last_error = error
            time.sleep(1 + attempt)
        if last_error is None:
            raise RuntimeError("Unknown SAM.gov error.")
        raise last_error


    def _curl_text(self, url: str) -> str:
        return self._curl_bytes(url, follow_redirects=False).decode("utf-8", errors="ignore")

    def _curl_headers(self, url: str) -> str:
        completed = subprocess.run(
            ["curl", "-sSI", "-m", str(self.timeout_seconds), url],
            check=True,
            capture_output=True,
        )
        return completed.stdout.decode("utf-8", errors="ignore")

    def _curl_bytes(self, url: str, *, follow_redirects: bool) -> bytes:
        args = ["curl", "-sS", "-m", str(self.timeout_seconds)]
        if follow_redirects:
            args.append("-L")
        args.append(url)
        completed = subprocess.run(
            args,
            check=True,
            capture_output=True,
        )
        return completed.stdout


def parse_headers(raw_headers: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in raw_headers.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def extract_filename(headers: dict[str, str], url: str) -> str:
    disposition = headers.get("content-disposition", "")
    match = re.search(r'filename="?([^"]+)"?', disposition)
    if match:
        return match.group(1).replace("/", "-")
    return url.rstrip("/").split("/")[-1] or "attachment.bin"


def is_retryable_payload(payload: dict[str, Any]) -> bool:
    status = payload.get("status")
    if isinstance(status, int) and status >= 500:
        return True
    error_code = str(payload.get("errorCode", "")).lower()
    error_name = str(payload.get("error", "")).lower()
    error_message = str(payload.get("errorMessage", "")).lower()
    combined = " ".join(part for part in (error_code, error_name, error_message) if part)
    return "internal server error" in combined
