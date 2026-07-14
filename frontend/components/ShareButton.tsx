"use client";

import { useState } from "react";

type ShareButtonProps = {
  title: string;
  text?: string;
};

export default function ShareButton({ title, text }: ShareButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleShare() {
    const url = window.location.href;

    if (navigator.share) {
      try {
        await navigator.share({ title, text, url });
      } catch (error) {
        if ((error as DOMException)?.name !== "AbortError") {
          console.error("Falha ao compartilhar", error);
        }
      }
      return;
    }

    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Falha ao copiar link", error);
    }
  }

  return (
    <button
      className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 dark:border-stone-600 dark:text-slate-300"
      onClick={handleShare}
      type="button"
    >
      <svg aria-hidden="true" fill="none" height="16" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" width="16" xmlns="http://www.w3.org/2000/svg">
        <circle cx="18" cy="5" r="3" />
        <circle cx="6" cy="12" r="3" />
        <circle cx="18" cy="19" r="3" />
        <line x1="8.59" x2="15.42" y1="10.51" y2="6.49" />
        <line x1="8.59" x2="15.42" y1="13.49" y2="17.51" />
      </svg>
      {copied ? "Link copiado!" : "Compartilhar"}
    </button>
  );
}
