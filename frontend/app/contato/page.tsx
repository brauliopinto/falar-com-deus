"use client";

import { useState } from "react";
import { enviarContato } from "@/lib/api";

type FormState = "idle" | "loading" | "success" | "error";

export default function ContatoPage() {
  const [state, setState] = useState<FormState>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [form, setForm] = useState({ nome: "", email: "", assunto: "", mensagem: "" });

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setState("loading");
    setErrorMsg("");
    try {
      await enviarContato(form);
      setState("success");
      setForm({ nome: "", email: "", assunto: "", mensagem: "" });
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Erro ao enviar mensagem.");
      setState("error");
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-stone-600 dark:bg-stone-700 dark:text-stone-100 dark:placeholder:text-stone-400 dark:focus:border-[#c49a5a] dark:focus:ring-[#c49a5a]";

  return (
    <main className="mx-auto max-w-2xl px-4 py-8 space-y-6">
      <header className="rounded-2xl border border-stone-300 bg-white p-8 shadow-sm dark:border-stone-700 dark:bg-stone-800">
        <p className="text-sm uppercase tracking-wider text-stone-500 dark:text-stone-400">Fale conosco</p>
        <p className="mt-2 text-base text-stone-600 dark:text-stone-400">
          Envie sugestões, críticas ou mensagens. Responderei assim que possível.
        </p>
      </header>

      <div className="rounded-2xl border border-stone-300 bg-white p-8 shadow-sm dark:border-stone-700 dark:bg-stone-800">
        {state === "success" ? (
          <div className="space-y-4 text-center">
            <p className="text-2xl">✉️</p>
            <p className="text-lg font-semibold text-stone-900 dark:text-stone-100">Mensagem enviada!</p>
            <p className="text-sm text-stone-600 dark:text-stone-400">
              Obrigado pelo contato. Sua mensagem foi recebida com sucesso.
            </p>
            <button
              className="mt-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-stone-600 dark:text-slate-300 dark:hover:bg-stone-700"
              onClick={() => setState("idle")}
              type="button"
            >
              Enviar outra mensagem
            </button>
          </div>
        ) : (
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300" htmlFor="nome">
                  Nome
                </label>
                <input
                  className={inputClass}
                  id="nome"
                  minLength={2}
                  name="nome"
                  onChange={handleChange}
                  placeholder="Seu nome"
                  required
                  type="text"
                  value={form.nome}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300" htmlFor="email">
                  E-mail
                </label>
                <input
                  className={inputClass}
                  id="email"
                  name="email"
                  onChange={handleChange}
                  placeholder="seu@email.com"
                  required
                  type="email"
                  value={form.email}
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300" htmlFor="assunto">
                Assunto
              </label>
              <input
                className={inputClass}
                id="assunto"
                minLength={3}
                name="assunto"
                onChange={handleChange}
                placeholder="Assunto da mensagem"
                required
                type="text"
                value={form.assunto}
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300" htmlFor="mensagem">
                Mensagem
              </label>
              <textarea
                className={`${inputClass} min-h-[160px] resize-y`}
                id="mensagem"
                minLength={10}
                name="mensagem"
                onChange={handleChange}
                placeholder="Escreva sua mensagem..."
                required
                value={form.mensagem}
              />
            </div>

            {state === "error" && (
              <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
                {errorMsg}
              </p>
            )}

            <button
              className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 dark:bg-[#7c5c2e]"
              disabled={state === "loading"}
              type="submit"
            >
              {state === "loading" ? "Enviando..." : "Enviar mensagem"}
            </button>

            <p className="text-center text-xs text-slate-400 dark:text-stone-500">
              Seus dados serão utilizados exclusivamente para responder à sua mensagem. As informações ficam armazenadas apenas na caixa de e-mail do responsável pelo site.
            </p>
          </form>
        )}
      </div>
    </main>
  );
}
