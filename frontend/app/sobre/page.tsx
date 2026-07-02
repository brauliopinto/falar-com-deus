import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Sobre — Falar com Deus",
  description: "Sobre o site Falar com Deus e a obra original Hablar con Dios de Francisco Fernández-Carvajal.",
};

export default function SobrePage() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-8 space-y-6">
      <header className="rounded-2xl border border-stone-300 bg-white p-8 shadow-sm dark:border-stone-700 dark:bg-stone-800">
        <p className="text-sm uppercase tracking-wider text-stone-500 dark:text-stone-400">Sobre este <em>site</em></p>
        <p className="mt-2 text-base text-stone-600 dark:text-stone-400">
          Meditações diárias traduzidas para o português a partir da obra original em espanhol.
        </p>
      </header>

      <article className="rounded-2xl border border-stone-300 bg-white p-8 shadow-sm space-y-8 text-slate-800 dark:border-stone-700 dark:bg-stone-800 dark:text-slate-200">

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-stone-900 dark:text-stone-100">O que é este <em>site</em></h2>
          <p className="leading-relaxed text-justify">
            Este <em>site</em> disponibiliza, em português, as meditações diárias da obra{" "}
            <em>Falar com Deus</em> — uma coleção de reflexões espirituais para cada dia do ano
            litúrgico, organizadas em três partes que convidam à leitura pausada, à oração e ao
            exame de consciência.
          </p>
          <p className="leading-relaxed text-justify">
            O conteúdo é obtido diariamente do <em>site</em> original em espanhol e traduzido
            automaticamente para o português, tornando esta espiritualidade acessível a leitores
            lusófonos. O arquivo permite também acessar meditações de dias anteriores.
          </p>
        </section>

        <hr className="border-slate-100 dark:border-stone-700" />

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-stone-900 dark:text-stone-100">A obra original</h2>
          <p className="leading-relaxed text-justify">
            <em>Hablar con Dios</em> é uma coleção de sete volumes de meditações escritas por{" "}
            <strong>Francisco Fernández-Carvajal</strong> (1938–2021), sacerdote do Opus Dei e
            prolífico autor de espiritualidade cristã. A obra foi publicada pela editora{" "}
            <strong>Ediciones Palabra</strong> (Madrid) e tornou-se uma das mais difundidas obras
            de meditação diária no mundo católico de língua espanhola, com traduções em dezenas de
            idiomas.
          </p>
          <p className="leading-relaxed text-justify">
            Cada meditação está dividida em três partes — seguindo a tradição da oração
            contemplativa —, acompanhadas de uma leitura litúrgica de referência e de citações de
            santos, papas e escrituras.
          </p>
          <a
            className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline dark:text-[#c49a5a]"
            href="https://hablarcondios.org"
            rel="noopener noreferrer"
            target="_blank"
          >
            Acessar o <em>site</em> original em espanhol →
          </a>
        </section>

        <hr className="border-slate-100 dark:border-stone-700" />

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-stone-900 dark:text-stone-100">Direitos e autoria</h2>
          <p className="leading-relaxed text-justify">
            Todo o conteúdo das meditações — textos, estrutura e citações — é de autoria de{" "}
            <strong>Francisco Fernández-Carvajal</strong> e propriedade intelectual de{" "}
            <strong>Ediciones Palabra, S.A.</strong> e dos detentores dos direitos da obra{" "}
            <em>Hablar con Dios</em>. A fonte primária das meditações diárias disponíveis neste
            <em>site</em> é o portal{" "}
            <a
              className="font-medium text-primary hover:underline dark:text-[#c49a5a]"
              href="https://hablarcondios.org"
              rel="noopener noreferrer"
              target="_blank"
            >
              hablarcondios.org
            </a>
            .
          </p>
          <p className="leading-relaxed text-justify">
            Este <em>site</em> é um projeto pessoal, sem fins comerciais, criado exclusivamente para
            facilitar o acesso à meditação diária em língua portuguesa. Não possui qualquer
            vínculo oficial com os autores, a editora ou o <em>site</em> original. Nenhum conteúdo é
            modificado intencionalmente em seu sentido; a tradução é automática e pode conter
            imperfeições.
          </p>
          <p className="leading-relaxed text-justify">
            Caso os titulares dos direitos desejem solicitar a remoção do conteúdo, a solicitação
            será atendida imediatamente.
          </p>
        </section>

        <hr className="border-slate-100 dark:border-stone-700" />

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-stone-900 dark:text-stone-100">Tradução</h2>
          <p className="leading-relaxed text-justify">
            As meditações são traduzidas do espanhol para o português do Brasil por meio do
            serviço <strong>DeepL</strong>, preservando a estrutura original dos textos, incluindo
            citações em itálico e referências bibliográficas.
          </p>
        </section>

      </article>

      <div className="flex justify-center">
        <Link
          className="rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-white hover:opacity-90"
          href="/"
        >
          Ir para a meditação de hoje
        </Link>
      </div>
    </main>
  );
}
