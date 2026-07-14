import type { Metadata } from "next";
import Link from "next/link";

import ShareButton from "@/components/ShareButton";
import { getMeditacaoPorData, listMeditacoes } from "@/lib/api";
import {
  buildReferenceList,
  getSelectedText,
  normalizeMeditationOrder,
  renderTextWithReferences,
  splitSectionSubtitle,
  splitReflectionAndCitations,
  shouldShowSubtitle,
  stripItalicMarkers
} from "@/lib/meditation";

type ArchivePageProps = {
  searchParams?: {
    date?: string;
    dateIso?: string;
    lang?: string;
    page?: string;
  };
};

function toApiDate(dateIso: string): string | null {
  const parts = dateIso.split("-");
  if (parts.length !== 3) {
    return null;
  }
  const [year, month, day] = parts;
  if (!year || !month || !day) {
    return null;
  }
  return `${day}/${month}/${year}`;
}

function toIsoDate(date: string): string {
  const [day, month, year] = date.split("/");
  if (!day || !month || !year) {
    return "";
  }
  return `${year}-${month}-${day}`;
}

function createArchiveQuery(options: { date?: string; lang: "pt" | "es"; page?: number }) {
  const params = new URLSearchParams({ lang: options.lang });
  if (options.date) {
    params.set("date", options.date);
  }
  if (options.page && options.page > 1) {
    params.set("page", String(options.page));
  }
  return `/arquivo?${params.toString()}`;
}

export async function generateMetadata({ searchParams }: ArchivePageProps): Promise<Metadata> {
  const lang = searchParams?.lang === "es" ? "es" : "pt";
  const pageNumber = Math.max(1, Number.parseInt(searchParams?.page ?? "1", 10) || 1);
  const offset = (pageNumber - 1) * 5;
  const requestedDate =
    searchParams?.date ?? (searchParams?.dateIso ? toApiDate(searchParams.dateIso) : null);

  const current = requestedDate
    ? await getMeditacaoPorData(requestedDate)
    : (await listMeditacoes(5, offset)).items[0] ?? null;

  if (!current) {
    return {};
  }

  const text = getSelectedText(current, lang);
  const title = stripItalicMarkers(text.titulo);
  const description = shouldShowSubtitle(text.subtitulo)
    ? stripItalicMarkers(text.subtitulo)
    : `Meditação de ${current.data}.`;

  return { title: `${title} | Falar com Deus`, description };
}

export default async function ArchivePage({ searchParams }: ArchivePageProps) {
  const lang = searchParams?.lang === "es" ? "es" : "pt";
  const pageNumber = Math.max(1, Number.parseInt(searchParams?.page ?? "1", 10) || 1);
  const limit = 5;
  const offset = (pageNumber - 1) * limit;
  const requestedDate =
    searchParams?.date ?? (searchParams?.dateIso ? toApiDate(searchParams.dateIso) : null);

  const [lista, requestedMeditation] = await Promise.all([
    listMeditacoes(limit, offset),
    requestedDate ? getMeditacaoPorData(requestedDate) : Promise.resolve(null)
  ]);

  const current = requestedMeditation ?? lista.items[0] ?? null;
  if (!current) {
    return (
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-stone-700 dark:bg-stone-800">
          <h1 className="text-2xl font-semibold text-primary">Arquivo de Meditações</h1>
          <p className="mt-3 text-slate-700 dark:text-slate-300">Ainda não existem meditações salvas.</p>
        </div>
      </main>
    );
  }

  const sortedItems = [...lista.items].sort((a, b) => {
    const toTs = (d: string) => {
      const [day, month, year] = d.split("/");
      return new Date(`${year}-${month}-${day}`).getTime();
    };
    return toTs(b.data) - toTs(a.data);
  });
  const currentIndex = sortedItems.findIndex((item) => item.data === current.data);
  const nextMeditation = currentIndex > 0 ? sortedItems[currentIndex - 1] : null;
  const prevMeditation =
    currentIndex >= 0 && currentIndex < sortedItems.length - 1 ? sortedItems[currentIndex + 1] : null;

  const totalPages = Math.max(1, Math.ceil(lista.total / lista.limit));
  let text = normalizeMeditationOrder(getSelectedText(current, lang));
  const { reflectionText, citations, appendix } = splitReflectionAndCitations(text.conteudoIII);
  text = { ...text, conteudoIII: reflectionText };
  const secI = splitSectionSubtitle(text.conteudoI);
  const secII = splitSectionSubtitle(text.conteudoII);
  const secIII = splitSectionSubtitle(text.conteudoIII);
  const references = buildReferenceList(citations);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-6 rounded-2xl border border-stone-300 bg-white p-4 shadow-sm sm:p-8 dark:border-stone-700 dark:bg-stone-800">
        <p className="text-sm uppercase tracking-wider text-stone-500 dark:text-stone-400">Meditações por dia</p>
        <p className="mt-2 text-base text-stone-600 dark:text-stone-400">Navegue no histórico e abra uma data específica.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4">
          <section className="rounded-2xl border border-stone-300 bg-white p-4 shadow-sm dark:border-stone-700 dark:bg-stone-800">
            <p className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">Histórico</p>
            <form action="/arquivo" className="space-y-2">
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-stone-600 dark:bg-stone-700 dark:text-stone-100"
                defaultValue={toIsoDate(current.data)}
                name="dateIso"
                type="date"
              />
              <input name="lang" type="hidden" value={lang} />
              <button className="w-full rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white dark:bg-[#c49a5a] dark:text-stone-900" type="submit">
                Buscar meditação
              </button>
            </form>
          </section>

          <section className="rounded-2xl border border-stone-300 bg-white p-4 shadow-sm dark:border-stone-700 dark:bg-stone-800">
            <p className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">Meditações nesta página</p>
            <ul className="space-y-2">
              {sortedItems.map((item) => (
                <li key={item.id}>
                  <Link
                    className={`block rounded-lg px-3 py-2 text-sm ${
                      item.data === current.data
                        ? "bg-blue-50 font-semibold text-primary dark:bg-amber-950 dark:text-[#c49a5a]"
                        : "text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-stone-700"
                    }`}
                    href={createArchiveQuery({ date: item.data, lang, page: pageNumber })}
                  >
                    {item.data}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </aside>

        <article className="space-y-6 rounded-2xl border border-stone-300 bg-white p-4 shadow-sm sm:p-8 dark:border-stone-700 dark:bg-stone-800">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">{current.data}</p>
              <h2 className="mt-1 text-2xl font-bold text-primary sm:text-3xl dark:text-[#c49a5a]">{renderTextWithReferences(text.titulo)}</h2>
              {shouldShowSubtitle(text.subtitulo) ? (
                <p className="mt-2 text-lg italic text-stone-700 dark:text-stone-300">{stripItalicMarkers(text.subtitulo)}</p>
              ) : null}
              <p className="mt-2 text-sm font-medium text-slate-500 dark:text-slate-400">
                {renderTextWithReferences(text.leituraRef)}
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <ShareButton text={current.data} title={stripItalicMarkers(text.titulo)} />
              {prevMeditation ? (
                <Link
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 dark:border-stone-600 dark:text-slate-300"
                  href={createArchiveQuery({ date: prevMeditation.data, lang, page: pageNumber })}
                >
                  Dia anterior
                </Link>
              ) : null}
              {nextMeditation ? (
                <Link
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 dark:border-stone-600 dark:text-slate-300"
                  href={createArchiveQuery({ date: nextMeditation.data, lang, page: pageNumber })}
                >
                  Dia seguinte
                </Link>
              ) : null}
              <Link
                className={`rounded-lg px-3 py-2 text-sm font-medium ${
                  lang === "pt" ? "bg-primary text-white" : "border border-slate-200 text-slate-700 dark:border-stone-600 dark:text-slate-300"
                }`}
                href={createArchiveQuery({ date: current.data, lang: "pt", page: pageNumber })}
              >
                Português
              </Link>
              <Link
                className={`rounded-lg px-3 py-2 text-sm font-medium ${
                  lang === "es" ? "bg-primary text-white" : "border border-slate-200 text-slate-700 dark:border-stone-600 dark:text-slate-300"
                }`}
                href={createArchiveQuery({ date: current.data, lang: "es", page: pageNumber })}
              >
                Espanhol
              </Link>
            </div>
          </div>

          <section className="space-y-4 text-slate-800 dark:text-slate-200">
            <nav className="flex flex-col gap-1 border-b border-slate-100 pb-4 text-sm font-medium dark:border-stone-700">
              <a href="#section-i" className="text-justify text-primary hover:underline dark:text-[#c49a5a]">
                I{secI.subtitle ? <>. {renderTextWithReferences(secI.subtitle)}</> : null}
              </a>
              <a href="#section-ii" className="text-justify text-primary hover:underline dark:text-[#c49a5a]">
                II{secII.subtitle ? <>. {renderTextWithReferences(secII.subtitle)}</> : null}
              </a>
              <a href="#section-iii" className="text-justify text-primary hover:underline dark:text-[#c49a5a]">
                III{secIII.subtitle ? <>. {renderTextWithReferences(secIII.subtitle)}</> : null}
              </a>
            </nav>
            <div id="section-i">
              <h3 className="text-lg font-bold text-justify">
                I{secI.subtitle ? <>. {renderTextWithReferences(secI.subtitle)}</> : null}
              </h3>
              <p className="whitespace-pre-line leading-relaxed text-justify">
                {renderTextWithReferences(secI.body || text.conteudoI, citations)}
              </p>
            </div>
            <div id="section-ii">
              <h3 className="text-lg font-bold text-justify">
                II{secII.subtitle ? <>. {renderTextWithReferences(secII.subtitle)}</> : null}
              </h3>
              <p className="whitespace-pre-line leading-relaxed text-justify">
                {renderTextWithReferences(secII.body || text.conteudoII, citations)}
              </p>
            </div>
            <div id="section-iii">
              <h3 className="text-lg font-bold text-justify">
                III{secIII.subtitle ? <>. {renderTextWithReferences(secIII.subtitle)}</> : null}
              </h3>
              <p className="whitespace-pre-line leading-relaxed text-justify">
                {renderTextWithReferences(secIII.body || text.conteudoIII, citations)}
              </p>
            </div>
            {references.length > 0 ? (
              <div className="border-t border-slate-100 pt-4 dark:border-stone-700">
                <h3 className="text-lg font-semibold text-justify">Referências citadas</h3>
                <ul className="mt-2 space-y-1">
                  {references.map((reference) => (
                    <li className="text-justify" id={reference.id} key={reference.id}>
                      <span className="text-slate-700 dark:text-slate-300">
                        <a href={`#cite-back-${reference.number}`} className="font-semibold text-primary hover:underline dark:text-[#c49a5a]" title="Voltar ao trecho">{reference.number}.</a>
                        {" "}{renderTextWithReferences(reference.label.slice(reference.number.length + 2))}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {appendix ? (
              <div className="border-t border-slate-100 pt-4 dark:border-stone-700">
                <p className="whitespace-pre-line text-sm leading-relaxed text-justify text-slate-600 dark:text-slate-400">
                  {renderTextWithReferences(appendix)}
                </p>
              </div>
            ) : null}
          </section>

          <footer className="flex items-center justify-between border-t border-slate-100 pt-4 dark:border-stone-700">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Página {pageNumber} de {totalPages}
            </p>
            <div className="flex gap-2">
              {pageNumber > 1 ? (
                <Link
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 dark:border-stone-600 dark:text-slate-300"
                  href={createArchiveQuery({ lang, page: pageNumber - 1 })}
                >
                  Página anterior
                </Link>
              ) : null}
              {pageNumber < totalPages ? (
                <Link
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 dark:border-stone-600 dark:text-slate-300"
                  href={createArchiveQuery({ lang, page: pageNumber + 1 })}
                >
                  Próxima página
                </Link>
              ) : null}
            </div>
          </footer>
        </article>
      </div>
    </main>
  );
}
