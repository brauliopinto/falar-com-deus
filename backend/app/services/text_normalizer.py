import html
import re
import unicodedata

MOJIBAKE_MARKERS = (
    # Ã followed by a continuation byte (actual mojibake of accented chars)
    # Standalone Ã is a legitimate Portuguese uppercase letter (e.g., SÃO) — excluded
    "Ã§",   # ç
    "Ã£",   # ã
    "Ãµ",   # õ
    "Ã©",   # é
    "Ã³",   # ó
    "Ã¡",   # á
    "Ã ",   # à
    "Ã­",   # í
    "Ãº",   # ú
    "Ãª",   # ê
    "Ã¢",   # â
    "Ã®",   # î
    "Ã´",   # ô
    "Ã»",   # û
    "Ã±",   # ñ
    "Ã¼",   # ü
    "Ã‡",   # Ç
    "Ã‚",   # Â (uppercase)
    "Â",    # non-breaking space and other Â mojibake
    "â€",   # curly quote start
    "â€™",  # '
    "â€œ",  # "
    "â€\x9d",  # "
)


_SUPERSCRIPT_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

# Contrações obrigatórias do português com a preposição "em".
# LLMs às vezes traduzem literalmente "en ella" → "em ela" em vez de "nela".
_EM_CONTRACTIONS: dict[str, str] = {
    "ela": "nela", "ele": "nele", "elas": "nelas", "eles": "neles",
    "o": "no", "a": "na", "os": "nos", "as": "nas",
    "um": "num", "uma": "numa", "uns": "nuns", "umas": "numas",
}
_EM_CONTRACTION_RE = re.compile(
    r"\b(em)\s+(" + "|".join(_EM_CONTRACTIONS) + r")\b",
    re.IGNORECASE,
)


def _apply_em_contraction(m: re.Match) -> str:
    replacement = _EM_CONTRACTIONS[m.group(2).lower()]
    return replacement[0].upper() + replacement[1:] if m.group(1)[0].isupper() else replacement


def _expand_superscript_digits(text: str) -> str:
    """Convert Unicode superscript digit sequences to space-padded regular digits."""
    return re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: f" {m.group().translate(_SUPERSCRIPT_DIGITS)} ", text)


def normalize_text(text: str) -> str:
    decoded = html.unescape(text).replace("\xa0", " ")
    decoded = (
        decoded.replace("\x91", "‘")
        .replace("\x92", "’")
        .replace("\x93", "“")
        .replace("\x94", "”")
        .replace("\x96", "-")
        .replace("\x97", "—")
    )
    expanded = _expand_superscript_digits(decoded)
    repaired = repair_mojibake(expanded)
    normalized = unicodedata.normalize("NFC", repaired)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = _EM_CONTRACTION_RE.sub(_apply_em_contraction, normalized)
    return normalized.strip()


def repair_mojibake(text: str) -> str:
    if not any(marker in text for marker in MOJIBAKE_MARKERS):
        return text

    candidates = [text]
    for encoding in ("latin-1", "cp1252"):
        repaired = text.encode(encoding, errors="ignore").decode("utf-8", errors="ignore")
        if repaired:
            candidates.append(repaired)

    def score(value: str) -> tuple[int, int]:
        marker_score = sum(value.count(marker) for marker in MOJIBAKE_MARKERS)
        return marker_score, -len(value)

    return min(candidates, key=score)
