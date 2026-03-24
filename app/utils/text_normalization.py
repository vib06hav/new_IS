import re
import unicodedata


_MOJIBAKE_REPLACEMENTS = {
    "â€™": "'",
    "â€˜": "'",
    "â€œ": '"',
    "â€": '"',
    "â€”": "-",
    "â€“": "-",
    "â€¦": "...",
    "\u2019": "'",
    "\u2018": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2014": "-",
    "\u2013": "-",
    "\u2026": "...",
}

_LIGATURE_REPLACEMENTS = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
}

_ZERO_WIDTH_CHARS = ("\u200b", "\u200c", "\u200d", "\ufeff")


def normalize_pdf_text(text: str) -> str:
    """Normalize extracted PDF text into a stable ASCII-friendly form."""
    if not text:
        return text

    normalized = text
    for char in _ZERO_WIDTH_CHARS:
        normalized = normalized.replace(char, "")
    for src, dest in _MOJIBAKE_REPLACEMENTS.items():
        normalized = normalized.replace(src, dest)
    normalized = unicodedata.normalize("NFKC", normalized)
    for src, dest in _LIGATURE_REPLACEMENTS.items():
        normalized = normalized.replace(src, dest)
    for src, dest in _MOJIBAKE_REPLACEMENTS.items():
        normalized = normalized.replace(src, dest)

    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = "\n".join(line.strip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def normalize_label(text: str) -> str:
    if not text:
        return ""
    normalized = normalize_pdf_text(text).lower()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"[\(\)\[\]:;,_/\\]+", " ", normalized)
    normalized = re.sub(r"\s*-\s*", "-", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip(" .-")


def has_mojibake(text: str) -> bool:
    if not text:
        return False
    return any(token in text for token in ("â€™", "â€˜", "â€œ", "â€", "â€”", "â€“", "â€¦"))
