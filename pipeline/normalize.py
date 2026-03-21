from __future__ import annotations

import json
import re
import subprocess
import zlib
from pathlib import Path
from typing import Iterable

from pipeline.fetch import FAMILY_LABELS
from pipeline.models import CorpusConfig, CorpusDocument, DocumentSection
from pipeline.text_utils import html_to_text, normalize_whitespace, stable_hash


def build_sections(
    config: CorpusConfig,
    repo_root: Path,
    documents: list[CorpusDocument],
) -> list[DocumentSection]:
    sections: list[DocumentSection] = []
    for document in documents:
        sections.extend(description_sections(document))
        for attachment in document.attachments:
            attachment_path = Path(attachment.raw_path)
            try:
                if attachment.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    sections.extend(docx_sections(document, attachment_path))
                elif attachment.content_type == "application/pdf":
                    sections.extend(pdf_sections(document, attachment_path))
                elif attachment.content_type in {"text/plain", "text/html"}:
                    sections.extend(text_attachment_sections(document, attachment_path, attachment.content_type))
            except Exception:
                continue

    output_root = repo_root / "data" / "normalized" / config.corpus_id
    output_root.mkdir(parents=True, exist_ok=True)
    output_path = output_root / "sections.jsonl"
    with output_path.open("w") as handle:
        for section in sections:
            handle.write(json.dumps(section.to_dict(), sort_keys=True) + "\n")
    return sections


def description_sections(document: CorpusDocument) -> list[DocumentSection]:
    if not document.description_html:
        return []

    output: list[DocumentSection] = []
    heading_pattern = re.compile(r"<h([1-4])[^>]*>(.*?)</h\1>", flags=re.IGNORECASE | re.DOTALL)
    matches = list(heading_pattern.finditer(document.description_html))
    if matches:
        for index, match in enumerate(matches, start=1):
            section_title = html_to_text(match.group(2)) or f"Description {index}"
            segment_start = match.end()
            segment_end = matches[index].start() if index < len(matches) else len(document.description_html)
            section_html = document.description_html[segment_start:segment_end]
            text = structured_html_to_text(section_html)
            if len(text) < 40:
                continue
            output.append(
                make_section(
                    document=document,
                    source_part="description",
                    section_key=f"description-{len(output) + 1:03d}",
                    section_title=section_title,
                    text=text,
                )
            )
    if output:
        return output

    fallback_text = structured_html_to_text(document.description_html)
    if not fallback_text:
        return []
    return [
        make_section(
            document=document,
            source_part="description",
            section_key="description-001",
            section_title="Description",
            text=fallback_text,
        )
    ]


def docx_sections(document: CorpusDocument, path: Path) -> list[DocumentSection]:
    completed = subprocess.run(
        ["/usr/bin/textutil", "-convert", "txt", "-stdout", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    text = completed.stdout
    if not text.strip():
        return []
    chunks = [normalize_whitespace(chunk) for chunk in re.split(r"\n\s*\n+", text) if normalize_whitespace(chunk)]
    if not chunks:
        chunks = list(chunk_text(normalize_whitespace(text), 1200))
    return [
        make_section(
            document=document,
            source_part=path.name,
            section_key=f"{path.stem}-{index:03d}",
            section_title=f"{path.name} part {index}",
            text=chunk,
        )
        for index, chunk in enumerate(chunks, start=1)
        if len(chunk) >= 40
    ]


def pdf_sections(document: CorpusDocument, path: Path) -> list[DocumentSection]:
    text = extract_pdf_text(path)
    if len(text) < 80:
        return []
    sections: list[DocumentSection] = []
    page_sections = split_pdf_text(text)
    for index, chunk in enumerate(page_sections, start=1):
        sections.append(
            make_section(
                document=document,
                source_part=path.name,
                section_key=f"{path.stem}-p001-{index:02d}",
                section_title=f"{path.name} extracted text",
                text=chunk,
            )
        )
    return sections


def text_attachment_sections(document: CorpusDocument, path: Path, content_type: str) -> list[DocumentSection]:
    text = path.read_text(errors="ignore")
    if content_type == "text/html":
        plain = html_to_text(text)
    else:
        plain = normalize_whitespace(text)
    if len(plain) < 40:
        return []
    chunks = chunk_text(plain, 1200)
    return [
        make_section(
            document=document,
            source_part=path.name,
            section_key=f"{path.stem}-{index:03d}",
            section_title=f"{path.name} part {index}",
            text=chunk,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]


def split_pdf_text(text: str) -> list[str]:
    lines = [line.strip() for line in re.split(r"\s{2,}|\n+", text) if line.strip()]
    chunks: list[str] = []
    current: list[str] = []
    for line in lines:
        if re.fullmatch(r"[A-Z0-9][A-Z0-9\s/\-]{8,}", line) and current:
            chunks.append(normalize_whitespace(" ".join(current)))
            current = [line.title()]
            continue
        current.append(line)
        if sum(len(item) for item in current) >= 1000:
            chunks.append(normalize_whitespace(" ".join(current)))
            current = []
    if current:
        chunks.append(normalize_whitespace(" ".join(current)))
    return [chunk for chunk in chunks if len(chunk) >= 80]


def chunk_text(text: str, max_chars: int) -> Iterable[str]:
    words = text.split()
    current: list[str] = []
    for word in words:
        current.append(word)
        if sum(len(item) + 1 for item in current) >= max_chars:
            yield " ".join(current)
            current = []
    if current:
        yield " ".join(current)


def extract_pdf_text(path: Path) -> str:
    pdf_bytes = path.read_bytes()
    extracted = extract_pdf_text_from_streams(pdf_bytes)
    if extracted:
        return extracted
    completed = subprocess.run(
        ["/usr/bin/strings", "-a", "-n", "6", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return normalize_whitespace(completed.stdout)


def extract_pdf_text_from_streams(pdf_bytes: bytes) -> str:
    chunks: list[str] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf_bytes, re.DOTALL):
        stream = match.group(1)
        try:
            data = zlib.decompress(stream)
        except zlib.error:
            continue
        if b"Tj" not in data and b"TJ" not in data:
            continue
        text = extract_text_operators(data.decode("latin1", errors="ignore"))
        if text:
            chunks.append(text)
    return normalize_whitespace(" ".join(chunks))


def extract_text_operators(content: str) -> str:
    fragments: list[str] = []
    index = 0
    while index < len(content):
        character = content[index]
        if character == "[":
            array_content, next_index = read_pdf_array(content, index)
            cursor = skip_pdf_whitespace(content, next_index)
            if content[cursor : cursor + 2] == "TJ":
                decoded = "".join(read_pdf_array_strings(array_content))
                if decoded:
                    fragments.append(decoded)
            index = next_index
            continue
        if character == "(":
            literal, next_index = read_pdf_literal_string(content, index)
            cursor = skip_pdf_whitespace(content, next_index)
            if content[cursor : cursor + 2] == "Tj":
                fragments.append(literal)
            index = next_index
            continue
        index += 1
    return " ".join(fragment.strip() for fragment in fragments if fragment.strip())


def read_pdf_array(content: str, start_index: int) -> tuple[str, int]:
    depth = 1
    cursor = start_index + 1
    while cursor < len(content) and depth > 0:
        if content[cursor] == "[":
            depth += 1
        elif content[cursor] == "]":
            depth -= 1
        cursor += 1
    return content[start_index + 1 : cursor - 1], cursor


def read_pdf_array_strings(array_content: str) -> list[str]:
    strings: list[str] = []
    cursor = 0
    while cursor < len(array_content):
        if array_content[cursor] == "(":
            literal, next_index = read_pdf_literal_string(array_content, cursor)
            if literal:
                strings.append(literal)
            cursor = next_index
            continue
        cursor += 1
    return strings


def read_pdf_literal_string(content: str, start_index: int) -> tuple[str, int]:
    cursor = start_index + 1
    depth = 1
    output: list[str] = []
    while cursor < len(content) and depth > 0:
        character = content[cursor]
        if character == "\\":
            cursor += 1
            if cursor >= len(content):
                break
            escaped = content[cursor]
            if escaped in {"\\", "(", ")"}:
                output.append(escaped)
            elif escaped == "n":
                output.append("\n")
            elif escaped == "r":
                output.append("\r")
            elif escaped == "t":
                output.append("\t")
            elif escaped == "b":
                output.append("\b")
            elif escaped == "f":
                output.append("\f")
            elif escaped in "01234567":
                octal_digits = escaped
                for _ in range(2):
                    if cursor + 1 < len(content) and content[cursor + 1] in "01234567":
                        cursor += 1
                        octal_digits += content[cursor]
                    else:
                        break
                output.append(chr(int(octal_digits, 8)))
            else:
                output.append(escaped)
            cursor += 1
            continue
        if character == "(":
            depth += 1
            output.append(character)
            cursor += 1
            continue
        if character == ")":
            depth -= 1
            cursor += 1
            if depth == 0:
                break
            output.append(")")
            continue
        output.append(character)
        cursor += 1
    return normalize_whitespace("".join(output)), cursor


def skip_pdf_whitespace(content: str, index: int) -> int:
    while index < len(content) and content[index].isspace():
        index += 1
    return index


def structured_html_to_text(html: str) -> str:
    table_pattern = re.compile(r"<table\b[^>]*>(.*?)</table>", flags=re.IGNORECASE | re.DOTALL)

    def replace_table(match: re.Match[str]) -> str:
        table_html = match.group(1)
        row_pattern = re.compile(r"<tr\b[^>]*>(.*?)</tr>", flags=re.IGNORECASE | re.DOTALL)
        cell_pattern = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", flags=re.IGNORECASE | re.DOTALL)
        row_texts: list[str] = []
        for row_html in row_pattern.findall(table_html):
            cells = [html_to_text(cell_html) for cell_html in cell_pattern.findall(row_html)]
            cells = [cell for cell in cells if cell]
            if cells:
                row_texts.append(" | ".join(cells))
        return " ; ".join(row_texts)

    without_tables = table_pattern.sub(replace_table, html)
    return html_to_text(without_tables)


def make_section(
    *,
    document: CorpusDocument,
    source_part: str,
    section_key: str,
    section_title: str,
    text: str,
) -> DocumentSection:
    family_hint = guess_family_hint(text)
    section_id = stable_hash(f"{document.notice_id}:{source_part}:{section_key}")
    return DocumentSection(
        section_id=section_id,
        notice_id=document.notice_id,
        title=document.title,
        posted_date=document.posted_date,
        family_hint=family_hint,
        source_part=source_part,
        section_key=section_key,
        section_title=section_title,
        section_text=normalize_whitespace(text),
        source_url=document.source_url,
    )


def guess_family_hint(text: str) -> str | None:
    lowered = text.lower()
    family_keywords = {
        "intake_routing": ["intake", "routing", "referral", "queue"],
        "records_documentation": ["record", "documentation", "document", "form"],
        "review_approval": ["review", "approval", "appeal", "authorize"],
        "reporting_compliance_support": ["report", "compliance", "audit", "dashboard"],
    }
    best_family: str | None = None
    best_score = 0
    for family_id, keywords in family_keywords.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_family = family_id
            best_score = score
    if best_family is None:
        return None
    return FAMILY_LABELS[best_family]
