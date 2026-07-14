import Link from "next/link";

import ShareButton from "@/components/ShareButton";
import { getMeditacaoHoje } from "@/lib/api";
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

type HomePageProps = {
  searchParams?: {
    lang?: string;
  };
};

function createQuery(lang: "pt" | "es"): string {
  const params = new URLSearchParams({ lang });
  return `/?${params.toString()}`;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const lang = searchParams?.lang === "es" ? "es" : "pt";
  const current = await getMeditacaoHoje();

  if (!current) {
    return (
      <main className="mx-auto max-w-5xl px-4 py-10">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-stone-700 dark:bg-stone-800">
          <h1 className="text-2xl font-semibold text-primary">Meditação Diária</h1>
          <p className="mt-3 text-slate-700 dark:text-slate-300">
            A meditação de hoje ainda não está disponível. A página será atualizada em breve.
          </p>
          <Link className="mt-4 inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white" href="/arquivo">
            Ir para o arquivo
          </Link>
        </div>
      </main>
    );
  }

  let text = normalizeMeditationOrder(getSelectedText(current, lang));
  const { reflectionText, citations, appendix } = splitReflectionAndCitations(text.conteudoIII);
  text = { ...text, conteudoIII: reflectionText };
  const secI = splitSectionSubtitle(text.conteudoI);
  const secII = splitSectionSubtitle(text.conteudoII);
  const secIII = splitSectionSubtitle(text.conteudoIII);
  const references = buildReferenceList(citations);

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <header className="mb-6 rounded-2xl border border-stone-300 bg-white p-4 shadow-sm sm:p-8 dark:border-stone-700 dark:bg-stone-800">
        <p className="text-sm uppercase tracking-wider text-stone-500 dark:text-stone-400">Meditação Diária</p>
        <p className="mt-2 text-base text-stone-600 dark:text-stone-400">Disponível em português e espanhol.</p>
      </header>

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
            <Link className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 dark:border-stone-600 dark:text-slate-300" href="/arquivo">
              Abrir arquivo
            </Link>
            <Link
              className={`rounded-lg px-3 py-2 text-sm font-medium ${
                lang === "pt" ? "bg-primary text-white" : "border border-slate-200 text-slate-700 dark:border-stone-600 dark:text-slate-300"
              }`}
              href={createQuery("pt")}
            >
              Português
            </Link>
            <Link
              className={`rounded-lg px-3 py-2 text-sm font-medium ${
                lang === "es" ? "bg-primary text-white" : "border border-slate-200 text-slate-700 dark:border-stone-600 dark:text-slate-300"
              }`}
              href={createQuery("es")}
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
      </article>
    </main>
  );
}
