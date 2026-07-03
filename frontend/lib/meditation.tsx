import { ReactNode } from "react";

import { Meditacao } from "@/types/meditacao";

export function getSelectedText(meditacao: Meditacao, lang: "pt" | "es") {
  if (lang === "es") {
    return {
      leituraRef: meditacao.leitura_ref,
      titulo: meditacao.titulo,
      subtitulo: meditacao.subtitulo,
      conteudoI: meditacao.conteudo_i,
      conteudoII: meditacao.conteudo_ii,
      conteudoIII: meditacao.conteudo_iii,
    };
  }

  return {
    leituraRef: meditacao.leitura_ref_pt || meditacao.leitura_ref,
    titulo: meditacao.titulo_pt,
    subtitulo: meditacao.subtitulo_pt,
    conteudoI: meditacao.conteudo_i_pt,
    conteudoII: meditacao.conteudo_ii_pt,
    conteudoIII: meditacao.conteudo_iii_pt,
  };
}

type SelectedText = ReturnType<typeof getSelectedText>;

export function stripItalicMarkers(text: string): string {
  return text.replace(/\*([^*\n]+)\*/g, "$1");
}

export function shouldShowSubtitle(subtitle: string): boolean {
  const normalized = subtitle
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
  if (!normalized) {
    return false;
  }
  return (
    !normalized.includes("nao encontrado") &&
    !normalized.includes("nao encontrada") &&
    !normalized.includes("no encontrado") &&
    !normalized.includes("no encontrada") &&
    !normalized.includes("legenda nao encontrada")
  );
}

const BOOKS = [
  "Gn",
  "Ex",
  "Lv",
  "Nm",
  "Dt",
  "Js",
  "Jz",
  "Rt",
  "1Sm",
  "2Sm",
  "1Rs",
  "2Rs",
  "1Cr",
  "2Cr",
  "Ed",
  "Ne",
  "Tb",
  "Jt",
  "Est",
  "Jó",
  "Sl",
  "Pr",
  "Ecl",
  "Ct",
  "Sb",
  "Eclo",
  "Is",
  "Jr",
  "Lm",
  "Br",
  "Ez",
  "Dn",
  "Os",
  "Jl",
  "Am",
  "Ab",
  "Jn",
  "Mq",
  "Na",
  "Hab",
  "Sf",
  "Ag",
  "Zc",
  "Ml",
  "Mt",
  "Mc",
  "Lc",
  "Jo",
  "At",
  "Rm",
  "1Cor",
  "2Cor",
  "Gl",
  "Ef",
  "Fl",
  "Cl",
  "1Ts",
  "2Ts",
  "1Tm",
  "2Tm",
  "Tt",
  "Fm",
  "Hb",
  "Tg",
  "1Pd",
  "2Pd",
  "1Jo",
  "2Jo",
  "3Jo",
  "Jd",
  "Ap"
] as const;

const BOOK_PATTERN = [...BOOKS]
  .sort((a, b) => b.length - a.length)
  .map((book) => book.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
  .join("|");

const REFERENCE_SINGLE_REGEX = new RegExp(
  `\\b(?:${BOOK_PATTERN}|[1-3]\\s+(?:Cor|Ts|Tm|Pd|Jo|Sm|Rs|Cr))\\.?\\s+\\d{1,3}(?:\\s*,\\s*\\d{1,3}(?:\\s*-\\s*\\d{1,3})?)?`
);

export type NumberedCitation = {
  number: string;
  text: string;
  biblicalReference: string | null;
};

export type ReferenceListItem = {
  id: string;
  number: string;
  label: string;
};

const SUPERSCRIPT_TO_DIGIT: Record<string, string> = {
  "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
  "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
};

function supToDigit(s: string): string {
  return s.split("").map((c) => SUPERSCRIPT_TO_DIGIT[c] ?? c).join("");
}

function parseItalicFromText(text: string, baseKey: number): ReactNode[] {
  if (!text.includes("*")) return [text];
  const parts = text.split(/(\*[^*\n]+\*)/g);
  const result: ReactNode[] = [];
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      result.push(<em key={`italic-${baseKey}-${i}`}>{part.slice(1, -1)}</em>);
    } else {
      result.push(part);
    }
  }
  return result;
}

function parseCitationMarkersFromText(text: string, citationNumbers: Set<string>): ReactNode[] {
  if (!text) return [text];
  if (citationNumbers.size === 0) {
    return parseItalicFromText(text, 0);
  }
  const options = [...citationNumbers].sort((a, b) => Number(b) - Number(a)).join("|");
  // Group 1: regular word-bounded digit  |  Group 2: Unicode superscript digit sequence
  const markerRegex = new RegExp(
    `\\b(${options})(?=\\b|[\\).,;:!?])|([⁰¹²³⁴⁵⁶⁷⁸⁹]+)`,
    "g"
  );
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let lastCitationSeen = 0;
  for (const match of text.matchAll(markerRegex)) {
    if (match.index === undefined) {
      continue;
    }
    const index = match.index;
    let citationNumber: string;
    let matchLength: number;
    if (match[1] !== undefined) {
      citationNumber = match[1];
      matchLength = match[1].length;
    } else {
      // Unicode superscript — convert to digits and check against known citations
      const converted = supToDigit(match[2]);
      if (!citationNumbers.has(converted)) {
        continue;
      }
      citationNumber = converted;
      matchLength = match[2].length;
    }
    const citNum = Number(citationNumber);
    // Require strictly ascending order: each citation must be greater than the last one seen.
    // This rejects numbers that appear in a non-citation context (e.g. "2 de outubro" after [6]
    // is rejected because 2 ≤ 6), while allowing gaps caused by inline markers omitted during
    // translation (e.g. [8] is accepted after [6] even if [7] was dropped by the translator).
    if (lastCitationSeen > 0 && citNum <= lastCitationSeen) {
      continue;
    }
    lastCitationSeen = citNum;
    if (index > lastIndex) {
      nodes.push(...parseItalicFromText(text.slice(lastIndex, index), lastIndex));
    }
    nodes.push(
      <a
        key={`citation-${citationNumber}-${index}`}
        id={`cite-back-${citationNumber}`}
        href={`#cit-${citationNumber}`}
        className="font-semibold text-primary underline decoration-blue-300 underline-offset-2"
      >
        [{citationNumber}]
      </a>
    );
    lastIndex = index + matchLength;
  }
  if (lastIndex < text.length) {
    nodes.push(...parseItalicFromText(text.slice(lastIndex), lastIndex));
  }
  return nodes;
}

export function renderTextWithReferences(
  text: string,
  citations: NumberedCitation[] = []
): ReactNode[] {
  if (!text) {
    return [text];
  }
  const citationNumbers = new Set(citations.map((item) => item.number));
  return parseCitationMarkersFromText(text, citationNumbers);
}

function isLikelySectionTitle(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed || trimmed.length > 80) {
    return false;
  }
  if (/[.!?]/.test(trimmed)) {
    return false;
  }
  const letters = trimmed.replace(/[^A-Za-zÁÉÍÓÚÜÑÇáéíóúüñç ]/g, "");
  if (!letters.trim()) {
    return false;
  }
  const alpha = [...letters].filter((ch) => /[A-Za-zÁÉÍÓÚÜÑÇáéíóúüñç]/.test(ch));
  const upper = alpha.filter((ch) => ch === ch.toUpperCase());
  return upper.length / Math.max(1, alpha.length) > 0.7;
}

function parseRomanSectionsBlock(text: string): { i: string; ii: string; iii: string } | null {
  if (!/\bI\s*[.\-]\s*/.test(text) || !/\bII\s*[.\-]\s*/.test(text) || !/\bIII\s*[.\-]\s*/.test(text)) {
    return null;
  }
  const chunks = text
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);
  const sections: Record<"I" | "II" | "III", string[]> = { I: [], II: [], III: [] };
  let current: "I" | "II" | "III" | null = null;
  for (const chunk of chunks) {
    const marker = chunk.match(/^(I|II|III)\s*[.\-]\s*(.*)$/);
    if (marker) {
      current = marker[1] as "I" | "II" | "III";
      const first = marker[2].trim();
      if (first) {
        sections[current].push(first);
      }
      continue;
    }
    if (current) {
      sections[current].push(chunk);
    }
  }
  if (!sections.I.length || !sections.II.length || !sections.III.length) {
    return null;
  }
  return {
    i: sections.I.join("\n\n"),
    ii: sections.II.join("\n\n"),
    iii: sections.III.join("\n\n")
  };
}

function cleanSummaryPrefix(value: string): string {
  return value.replace(/^[—\-]\s*/, "").trim();
}

function isSummaryLine(value: string): boolean {
  return /^[—\-]\s*\S+/.test(value.trim());
}

export function normalizeMeditationOrder(text: SelectedText): SelectedText {
  // When the scraper misses the I/II/III structure, all extra paragraphs end up
  // appended to conteudoIII. Detect and restructure that case here.
  const parts = text.conteudoIII
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);

  // Strip leading summary lines from conteudoIII to find the Roman-section body.
  // First summary → subtitle for section II; second summary → subtitle for section III.
  let skipCount = 0;
  let subtitleII = "";
  let subtitleIII = "";
  if (parts.length > skipCount && isSummaryLine(parts[skipCount])) {
    subtitleII = cleanSummaryPrefix(parts[skipCount]);
    skipCount++;
  }
  if (parts.length > skipCount && isSummaryLine(parts[skipCount])) {
    subtitleIII = cleanSummaryPrefix(parts[skipCount]);
    skipCount++;
  }

  const parsed = parseRomanSectionsBlock(parts.slice(skipCount).join("\n\n"));
  if (!parsed) {
    return text;
  }

  const subtitleI = isSummaryLine(text.conteudoII) ? cleanSummaryPrefix(text.conteudoII) : "";

  return {
    ...text,
    titulo: isLikelySectionTitle(text.conteudoI) ? text.conteudoI : text.titulo,
    conteudoI: subtitleI ? `— ${subtitleI}\n\n${parsed.i}` : parsed.i,
    conteudoII: subtitleII ? `— ${subtitleII}\n\n${parsed.ii}` : parsed.ii,
    conteudoIII: subtitleIII ? `— ${subtitleIII}\n\n${parsed.iii}` : parsed.iii,
  };
}

export function splitSectionSubtitle(content: string): { subtitle: string; body: string } {
  const parts = content
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);
  if (parts.length === 0) {
    return { subtitle: "", body: "" };
  }

  const first = parts[0];
  if (/^[—\-]\s*/.test(first) && parts.length > 1) {
    return {
      subtitle: first.replace(/^[—\-]\s*/, "").trim(),
      body: parts.slice(1).join("\n\n")
    };
  }

  // Detect author attribution lines in ALL CAPS (e.g., "SAN JOSEMARÍA ESCRIBÁ*")
  // that lost their "—" prefix during translation
  if (isLikelySectionTitle(first.replace(/\*+$/, "")) && parts.length > 1) {
    return {
      subtitle: first.replace(/\*+$/, "").trim(),
      body: parts.slice(1).join("\n\n")
    };
  }

  return { subtitle: "", body: content };
}

function extractBiblicalReference(value: string): string | null {
  const match = value.match(REFERENCE_SINGLE_REGEX);
  return match ? match[0].replace(/\s+/g, " ").trim() : null;
}

export function splitReflectionAndCitations(reflection: string): {
  reflectionText: string;
  citations: NumberedCitation[];
  appendix: string;
} {
  const startIndex = reflection.search(/\n\s*1\s+/);
  if (startIndex < 0) {
    return { reflectionText: reflection, citations: [], appendix: "" };
  }

  // The citation block is only the first \n\n-separated paragraph; subsequent paragraphs
  // (biography, appendix notes, etc.) must not bleed into the last citation entry.
  const citationSection = reflection.slice(startIndex).trim();
  const citationParagraphs = citationSection.split(/\n\n/);
  const possibleCitationBlock = citationParagraphs[0].replace(/\s*\n\s*/g, " ").trim();
  if (!/\b2\s+/.test(possibleCitationBlock)) {
    return { reflectionText: reflection, citations: [], appendix: "" };
  }

  const citationRegex = /(\d+)\s+(.+?)(?=\s+[—-]\s+\d+\s+|$)/g;
  const parsed: NumberedCitation[] = [];
  for (const match of possibleCitationBlock.matchAll(citationRegex)) {
    const number = match[1];
    const rawText = match[2].trim().replace(/\s+/g, " ");
    parsed.push({
      number,
      text: rawText,
      biblicalReference: extractBiblicalReference(rawText)
    });
  }

  if (parsed.length === 0) {
    return { reflectionText: reflection, citations: [], appendix: "" };
  }

  return {
    reflectionText: reflection.slice(0, startIndex).trim(),
    citations: parsed,
    appendix: citationParagraphs.slice(1).join("\n\n").trim(),
  };
}

export function buildReferenceList(citations: NumberedCitation[]): ReferenceListItem[] {
  const items: ReferenceListItem[] = [];
  const seenLabels = new Set<string>();

  for (const citation of citations) {
    const label = `${citation.number}. ${citation.text}`;
    if (seenLabels.has(label)) {
      continue;
    }
    seenLabels.add(label);
    items.push({
      id: `cit-${citation.number}`,
      number: citation.number,
      label
    });
  }

  return items;
}
