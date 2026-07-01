import type { Metadata } from "next";
import { Dancing_Script } from "next/font/google";
import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";
import ThemeToggle from "@/components/ThemeToggle";

const dancingScript = Dancing_Script({
  subsets: ["latin"],
  weight: ["700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Meditação Diária",
  description: "Meditação diária traduzida para português"
};

const themeScript = `
(function() {
  try {
    var t = localStorage.getItem('theme');
    if (t === 'dark' || (!t && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    }
  } catch(e) {}
})();
`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <div className="sticky top-0 z-50 border-b border-stone-300 bg-[#fbf8f2]/95 backdrop-blur-sm dark:border-stone-700 dark:bg-stone-950/95">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
            <Link className={`${dancingScript.className} text-3xl text-stone-900 dark:text-stone-100`} href="/">
              Falar com Deus
            </Link>
            <nav className="flex items-center gap-2">
              <Link className="rounded-lg px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100 dark:text-stone-300 dark:hover:bg-stone-800" href="/">
                Meditação do dia
              </Link>
              <Link
                className="rounded-lg px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100 dark:text-stone-300 dark:hover:bg-stone-800"
                href="/arquivo"
              >
                Meditações anteriores
              </Link>
              <Link
                className="rounded-lg px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100 dark:text-stone-300 dark:hover:bg-stone-800"
                href="/sobre"
              >
                Sobre
              </Link>
              <Link
                className="rounded-lg px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-100 dark:text-stone-300 dark:hover:bg-stone-800"
                href="/contato"
              >
                Contato
              </Link>
              <ThemeToggle />
            </nav>
          </div>
        </div>
        {children}
      </body>
    </html>
  );
}
