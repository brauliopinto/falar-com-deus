from dataclasses import dataclass
from datetime import datetime
import re
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from app.services.text_normalizer import normalize_text


@dataclass
class ScrapedMeditation:
    data: str
    titulo_raw: str
    titulo: str
    subtitulo_raw: str
    subtitulo: str
    leitura_ref_raw: str
    leitura_ref: str
    conteudo_i_raw: str
    conteudo_i: str
    conteudo_ii_raw: str
    conteudo_ii: str
    conteudo_iii_raw: str
    conteudo_iii: str


class ScraperService:
    def __init__(self, source_url: str) -> None:
        self._source_url = source_url

    def scrape_today(self) -> ScrapedMeditation:
        return self.scrape_for_date()

    def scrape_for_date(
        self,
        source_url: str | None = None,
        target_date: datetime | None = None,
    ) -> ScrapedMeditation:
        final_source_url = source_url or self._source_url
        scrape_date = target_date or datetime.now(ZoneInfo("America/Sao_Paulo"))
        response = requests.get(final_source_url, timeout=30)
        response.raise_for_status()
        encoding = response.apparent_encoding or response.encoding or "utf-8"
        html_text = response.content.decode(encoding, errors="replace")
        return self._parse_html(html_text, scrape_date=scrape_date)

    def _parse_html(self, html: str, scrape_date: datetime) -> ScrapedMeditation:
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article") or soup

        h1 = article.find("h1")
        h2 = article.find("h2")
        titulo_raw = h1.get_text(" ", strip=True) if h1 else "Meditación diaria"
        titulo = normalize_text(titulo_raw)
        subtitulo_raw = h2.get_text(" ", strip=True) if h2 else ""
        subtitulo = normalize_text(subtitulo_raw)

        # Extract (raw, normalized) pairs for every paragraph; filter by normalized non-empty.
        pairs = [self._paragraph_text(p) for p in article.find_all("p")]
        non_empty_pairs = [(r, n) for r, n in pairs if n]
        if not non_empty_pairs:
            raise ValueError("Não foi possível extrair conteúdo da meditação.")

        non_empty_raw = [r for r, n in non_empty_pairs]
        non_empty = [n for r, n in non_empty_pairs]

        leitura_ref_raw = non_empty_raw[0]
        leitura_ref = non_empty[0]
        remaining_raw = non_empty_raw[1:]
        remaining = non_empty[1:]

        if self._is_generic_title(titulo) and remaining and self._looks_like_meditation_title(remaining[0]):
            titulo = remaining[0]
            titulo_raw = remaining_raw[0]
            remaining = remaining[1:]
            remaining_raw = remaining_raw[1:]

        roman_start_idx = self._find_roman_section_start(remaining)
        if roman_start_idx is not None:
            pre_roman = remaining[:roman_start_idx]
            pre_roman_raw = remaining_raw[:roman_start_idx]

            # Decision-making on normalized; mirror indices to raw.
            summary_raw = [p for p in pre_roman if re.match(r"^[—\-]\s*\S", p)]
            header_items = [p for p in pre_roman if not re.match(r"^[—\-]\s*\S", p)]
            summary_raw_r = [pre_roman_raw[i] for i, p in enumerate(pre_roman) if re.match(r"^[—\-]\s*\S", p)]
            header_items_r = [pre_roman_raw[i] for i, p in enumerate(pre_roman) if not re.match(r"^[—\-]\s*\S", p)]

            summary_items = [self._clean_summary_marker(p) for p in summary_raw]
            summary_items_r = [self._clean_summary_marker(p) for p in summary_raw_r]

            if self._is_generic_title(titulo) and header_items:
                titulo = header_items[0]
                titulo_raw = header_items_r[0]
                if len(header_items) > 1 and not subtitulo:
                    subtitulo = header_items[1]
                    subtitulo_raw = header_items_r[1]
            elif header_items and not subtitulo:
                subtitulo = header_items[0]
                subtitulo_raw = header_items_r[0]

            roman_sections = self._extract_roman_sections(remaining[roman_start_idx:])
            roman_sections_r = self._extract_roman_sections(remaining_raw[roman_start_idx:])
            if roman_sections is not None and roman_sections_r is not None:
                sec_i, sec_ii, sec_iii = roman_sections
                sec_i_r, sec_ii_r, sec_iii_r = roman_sections_r
                if len(summary_items) >= 3 and all(summary_items):
                    conteudo_i = f"— {summary_items[0]}\n\n{sec_i}"
                    conteudo_ii = f"— {summary_items[1]}\n\n{sec_ii}"
                    conteudo_iii = f"— {summary_items[2]}\n\n{sec_iii}"
                    conteudo_i_r = f"— {summary_items_r[0]}\n\n{sec_i_r}"
                    conteudo_ii_r = f"— {summary_items_r[1]}\n\n{sec_ii_r}"
                    conteudo_iii_r = f"— {summary_items_r[2]}\n\n{sec_iii_r}"
                else:
                    conteudo_i, conteudo_ii, conteudo_iii = sec_i, sec_ii, sec_iii
                    conteudo_i_r, conteudo_ii_r, conteudo_iii_r = sec_i_r, sec_ii_r, sec_iii_r
                return ScrapedMeditation(
                    data=scrape_date.strftime("%d/%m/%Y"),
                    titulo_raw=titulo_raw,
                    titulo=titulo,
                    subtitulo_raw=subtitulo_raw,
                    subtitulo=subtitulo,
                    leitura_ref_raw=leitura_ref_raw,
                    leitura_ref=leitura_ref,
                    conteudo_i_raw=conteudo_i_r,
                    conteudo_i=conteudo_i,
                    conteudo_ii_raw=conteudo_ii_r,
                    conteudo_ii=conteudo_ii,
                    conteudo_iii_raw=conteudo_iii_r,
                    conteudo_iii=conteudo_iii,
                )

        summary_items = [self._clean_summary_marker(item) for item in remaining[:3]]
        summary_items_r = [self._clean_summary_marker(item) for item in remaining_raw[:3]]
        if len(summary_items) >= 3 and all(summary_items):
            conteudo_i, conteudo_ii, conteudo_iii = summary_items[:3]
            conteudo_i_r, conteudo_ii_r, conteudo_iii_r = summary_items_r[:3]
            extra_parts = remaining[3:]
            extra_parts_r = remaining_raw[3:]
        else:
            conteudo_i = remaining[0] if len(remaining) > 0 else ""
            conteudo_ii = remaining[1] if len(remaining) > 1 else ""
            conteudo_iii = remaining[2] if len(remaining) > 2 else ""
            conteudo_i_r = remaining_raw[0] if len(remaining_raw) > 0 else ""
            conteudo_ii_r = remaining_raw[1] if len(remaining_raw) > 1 else ""
            conteudo_iii_r = remaining_raw[2] if len(remaining_raw) > 2 else ""
            extra_parts = remaining[3:]
            extra_parts_r = remaining_raw[3:]

        if extra_parts:
            conteudo_iii = conteudo_iii + "\n\n" + "\n\n".join(extra_parts)
            conteudo_iii_r = conteudo_iii_r + "\n\n" + "\n\n".join(extra_parts_r)

        if not conteudo_i or not conteudo_ii or not conteudo_iii:
            raise ValueError("Estrutura da meditação não contém seções suficientes para I/II/III.")

        return ScrapedMeditation(
            data=scrape_date.strftime("%d/%m/%Y"),
            titulo_raw=titulo_raw,
            titulo=titulo,
            subtitulo_raw=subtitulo_raw,
            subtitulo=subtitulo,
            leitura_ref_raw=leitura_ref_raw,
            leitura_ref=leitura_ref,
            conteudo_i_raw=conteudo_i_r,
            conteudo_i=conteudo_i,
            conteudo_ii_raw=conteudo_ii_r,
            conteudo_ii=conteudo_ii,
            conteudo_iii_raw=conteudo_iii_r,
            conteudo_iii=conteudo_iii,
        )

    @staticmethod
    def _paragraph_text(p_tag) -> tuple[str, str]:
        """Return (raw, normalized) text. raw is plain text; normalized preserves
        <em>/<i> as *text* markdown and expands <sup> citation digits."""
        raw = p_tag.get_text(" ", strip=True)
        for em_tag in p_tag.find_all(["em", "i"]):
            em_tag.replace_with(f"*{em_tag.get_text()}*")
        for sup in p_tag.find_all("sup"):
            sup_text = sup.get_text().strip()
            if sup_text.isdigit():
                sup.replace_with(f" {sup_text} ")
        return raw, normalize_text(p_tag.get_text(" ", strip=True))

    @staticmethod
    def _is_generic_title(title: str) -> bool:
        normalized = title.strip().lower()
        return normalized in {
            "meditación diaria",
            "meditacion diaria",
            "meditação diária",
            "meditação diaria",
            "meditación día anterior",
            "meditacion dia anterior",
            "meditación día siguiente",
            "meditacion dia siguiente",
        }

    @staticmethod
    def _looks_like_meditation_title(value: str) -> bool:
        if len(value) > 80:
            return False
        if value.startswith(("—", "-", "I .", "II .", "III .")):
            return False
        letters = re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç ]", "", value)
        if not letters.strip():
            return False
        upper_ratio = sum(1 for ch in letters if ch.isupper()) / max(1, sum(1 for ch in letters if ch.isalpha()))
        return upper_ratio > 0.7

    @staticmethod
    def _clean_summary_marker(value: str) -> str:
        cleaned = re.sub(r"^[—\-]\s*", "", value).strip()
        return cleaned

    @staticmethod
    def _find_roman_section_start(values: list[str]) -> int | None:
        for idx, value in enumerate(values):
            if re.match(r"^(I|II|III)\s*[.\-]\s*", value):
                return idx
        return None

    @staticmethod
    def _extract_roman_sections(values: list[str]) -> tuple[str, str, str] | None:
        sections: dict[str, list[str]] = {"I": [], "II": [], "III": []}
        current: str | None = None
        for value in values:
            marker = re.match(r"^(I|II|III)\s*[.\-]\s*(.*)$", value)
            if marker:
                current = marker.group(1)
                first_chunk = marker.group(2).strip()
                if first_chunk:
                    sections[current].append(first_chunk)
                continue
            if current is not None:
                sections[current].append(value)

        if not sections["I"] or not sections["II"] or not sections["III"]:
            return None

        return (
            "\n\n".join(sections["I"]).strip(),
            "\n\n".join(sections["II"]).strip(),
            "\n\n".join(sections["III"]).strip(),
        )
