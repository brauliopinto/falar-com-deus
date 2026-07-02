import { Meditacao } from "@/types/meditacao";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getMeditacaoHoje(): Promise<Meditacao | null> {
  const response = await fetch(`${apiUrl}/meditacoes/hoje`, {
    cache: "no-store"
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Falha ao carregar meditação do dia.");
  }

  return (await response.json()) as Meditacao;
}

export async function getMeditacaoPorData(data: string): Promise<Meditacao | null> {
  const response = await fetch(`${apiUrl}/meditacoes/por-data?data=${encodeURIComponent(data)}`, {
    cache: "no-store"
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Falha ao carregar meditação pela data.");
  }

  return (await response.json()) as Meditacao;
}

type MeditacaoListResponse = {
  items: Meditacao[];
  total: number;
  limit: number;
  offset: number;
};

export async function listMeditacoes(limit = 30, offset = 0): Promise<MeditacaoListResponse> {
  const response = await fetch(`${apiUrl}/meditacoes/?limit=${limit}&offset=${offset}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Falha ao listar meditações.");
  }

  return (await response.json()) as MeditacaoListResponse;
}

export type ContatoPayload = {
  nome: string;
  email: string;
  assunto: string;
  mensagem: string;
};

export async function enviarContato(payload: ContatoPayload): Promise<void> {
  const response = await fetch(`/api/contato`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? "Erro ao enviar mensagem.");
  }
}
