from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from html.parser import HTMLParser
from html import unescape
from pathlib import Path


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "with",
}

OCR_CHAR_REPLACEMENTS = str.maketrans(
    {
        "\u0091": "'",
        "\u0092": "'",
        "\u0093": '"',
        "\u0094": '"',
        "\u0096": "-",
        "\u0097": "-",
        "\u00a0": " ",
        "\u00ad": "",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
    }
)

CORPUS_OCR_REPAIRS = {
    "High-CostMedication": "High-Cost Medication",
    "concerningthe": "concerning the",
    "VAstaff": "VA staff",
    "providedaccess": "provided access",
    "bythe": "by the",
    "willbesubmitted": "will be submitted",
    "toappeals": "to appeals",
    "at leas t": "at least",
    "prio r": "prior",
    "Medica l": "Medical",
    "VAstaff": "VA staff",
    "itsoffices": "its offices",
    "allreasonable": "all reasonable",
    "thiscontract": "this contract",
    "suchappeals": "such appeals",
    "claimsare": "claims are",
    "completelyor": "completely or",
    "Ifthe": "If the",
    "issubject": "is subject",
    "toverify": "to verify",
    "besubmitted": "be submitted",
    "patien t": "patient",
}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def html_to_text(html: str) -> str:
    parser = HTMLToTextParser()
    parser.feed(html or "")
    parser.close()
    return normalize_whitespace(parser.get_text())


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def slugify(text: str) -> str:
    compact = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return compact.strip("-") or "item"


def simple_stem(token: str) -> str:
    if len(token) <= 4:
        return token
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def tokenize(text: str) -> list[str]:
    clean = re.sub(r"[^a-z0-9]+", " ", text.lower())
    tokens = [simple_stem(part) for part in clean.split() if len(part) > 2]
    return [token for token in tokens if token not in STOPWORDS]


def sentence_split(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n{2,}", normalize_whitespace(text))
    results = []
    for chunk in chunks:
        cleaned = chunk.strip(" -\t")
        if cleaned:
            results.append(cleaned)
    return results


def canonicalize_requirement(text: str) -> str:
    normalized = unescape(text.lower())
    normalized = re.sub(
        r"\b(contractor|vendor|offeror|quoter|successful offeror|successful contractor)\b",
        "contractor",
        normalized,
    )
    normalized = re.sub(r"\bva\b|\bveterans affairs\b", "agency", normalized)
    normalized = re.sub(r"\b\d+(?:\.\d+)?\b", " ", normalized)
    normalized = re.sub(r"[^a-z\s]+", " ", normalized)
    return normalize_whitespace(normalized)


def clean_ocr_text(text: str) -> str:
    cleaned = text.translate(OCR_CHAR_REPLACEMENTS)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", cleaned)
    cleaned = re.sub(r"\b([A-Z]{2,})([a-z]{2,})\b", r"\1 \2", cleaned)
    cleaned = re.sub(r"(?<=[:;,.])(?=[A-Za-z])", " ", cleaned)
    cleaned = re.sub(r"(?<=\))(?=[A-Za-z])", " ", cleaned)
    cleaned = re.sub(r"(?<=[A-Za-z])(?=\()", " ", cleaned)
    for source, replacement in CORPUS_OCR_REPAIRS.items():
        cleaned = cleaned.replace(source, replacement)
    return normalize_whitespace(cleaned)


def counter_cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in overlap)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def phrase_counts(texts: list[str], size: int = 2) -> Counter[str]:
    phrases: Counter[str] = Counter()
    for text in texts:
        tokens = tokenize(text)
        if len(tokens) < size:
            continue
        for index in range(0, len(tokens) - size + 1):
            phrase = " ".join(tokens[index : index + size])
            phrases[phrase] += 1
    return phrases


def title_case_phrase(phrase: str) -> str:
    return " ".join(word.capitalize() for word in phrase.split())


def read_text_file(path: Path) -> str:
    return path.read_text(errors="ignore")


class HTMLToTextParser(HTMLParser):
    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "dt",
        "dd",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "nav",
        "p",
        "section",
        "table",
        "tr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if data:
            self._chunks.append(data)

    def get_text(self) -> str:
        return "".join(self._chunks)
