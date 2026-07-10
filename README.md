# Falar com Deus

Aplicação web para leitura diária das meditações de *Hablar con Dios*, de **Francisco Fernández-Carvajal** (Ediciones Palabra), traduzidas automaticamente para o português do Brasil.

O conteúdo é obtido diariamente da própria versão em português do portal [hablarcondios.org](https://hablarcondios.org/pt/meditacao-diaria/). Caso essa página falhe, o sistema recorre à versão em espanhol e traduz automaticamente para o português do Brasil por um modelo de linguagem especializado em linguagem sacra (via **OpenRouter**, com fallback para **DeepL**). O conteúdo é servido em uma interface com imagem de fundo sacra, modo noturno e responsividade mobile.

> **Aviso de direitos:** todo o conteúdo das meditações é propriedade intelectual de Francisco Fernández-Carvajal e Ediciones Palavra, S.A. Este projeto é pessoal, sem fins comerciais e sem vínculo oficial com os titulares dos direitos.

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLAlchemy · Alembic · APScheduler |
| Scraping | BeautifulSoup4 · Requests |
| Tradução | OpenRouter (LangChain) · DeepL — usados apenas como fallback quando a página em português falha |
| Banco de dados | PostgreSQL 16 |
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS |
| Infraestrutura | Docker · Docker Compose |

---

## Arquitetura

```
hablarcondios.org/pt/meditacao-diaria/  (fonte primária, já em português)
      │
      ▼ HTTP scrape (00:17 BRT — até 3 tentativas: 00:17, 03:17, 06:17)
      │
      ├─ sucesso ──► campos *_pt = texto PT direto (sem tradução)
      │                │
      │                └─► também raspa hablarcondios.org/meditacion-diaria/ (ES)
      │                    só para preencher os campos originais (sem traduzir),
      │                    mantendo o toggle PT/ES do frontend funcional
      │                    (se essa raspagem ES falhar, os campos originais
      │                    ficam como cópia do texto PT)
      │
      └─ falha ──► hablarcondios.org/meditacion-diaria/ (fallback, em espanhol)
                          │
                          ▼  OpenRouter (LLM) / DeepL (fallback)
                    ┌──────────────┐
                    │  Translator  │
                    └──────────────┘
                          │ campos *_pt = texto traduzido
      │
      ▼
┌─────────────────┐
│   PostgreSQL    │  tabela: meditacoes
└─────────────────┘
      │ REST API
      ▼
┌─────────────────┐
│  FastAPI (8000) │  /meditacoes/hoje · /meditacoes/por-data · /meditacoes/ · /contato/
└─────────────────┘
      │ fetch (SSR)
      ▼
┌─────────────────┐
│  Next.js (3000) │  / · /arquivo · /sobre · /contato
└─────────────────┘
```

---

## Estrutura do projeto

```
falar-com-deus/
├── docker-compose.yml
├── .vscode/
│   └── settings.json             # desativa linter CSS nativo (compatibilidade Tailwind)
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── .env.example
│   ├── alembic/
│   │   └── versions/
│   │       ├── 20260627_0001_create_meditacoes.py
│   │       ├── 20260628_0001_add_raw_columns.py
│   │       ├── 20260628_0002_drop_reflexao_columns.py
│   │       └── 20260628_0003_add_leitura_ref_pt.py
│   ├── scripts/
│   │   └── editar_meditacao.py   # edição manual de registros via CLI
│   └── app/
│       ├── main.py               # inicialização FastAPI + scheduler
│       ├── core/
│       │   ├── config.py         # Settings via pydantic-settings
│       │   ├── logging.py
│       │   └── security.py       # validação do X-API-Key
│       ├── db/
│       │   ├── base.py           # Base declarativa SQLAlchemy
│       │   └── session.py        # engine + SessionLocal
│       ├── models/
│       │   └── meditacao.py      # modelo ORM da tabela meditacoes
│       ├── schemas/
│       │   ├── meditacao.py      # schemas Pydantic (request/response)
│       │   └── contato.py        # schema do formulário de contato
│       ├── api/routes/
│       │   ├── meditacoes.py     # endpoints REST de meditações
│       │   └── contato.py        # endpoint POST /contato/
│       └── services/
│           ├── scraper.py        # raspagem HTML + parsing
│           ├── text_normalizer.py # limpeza de mojibake, HTML entities, unicode
│           ├── translator.py     # tradução via OpenRouter (LangChain) com fallback DeepL
│           ├── meditation_service.py # orquestração (scrape → traduz → persiste)
│           ├── email_service.py  # envio de e-mail via SMTP
│           └── scheduler.py      # APScheduler — 3 tentativas diárias (00:17, 03:17, 06:17)
└── frontend/
    ├── Dockerfile
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── public/
    │   └── falar_com_deus.png    # imagem de fundo sacra
    ├── app/
    │   ├── layout.tsx            # navbar + MobileNav + ThemeToggle + script anti-flash
    │   ├── globals.css           # estilos globais, fundo, cards translúcidos
    │   ├── page.tsx              # meditação do dia
    │   ├── arquivo/page.tsx      # arquivo com navegação por data
    │   ├── sobre/page.tsx        # apresentação e direitos autorais
    │   ├── contato/page.tsx      # formulário de contato
    │   └── api/contato/route.ts  # proxy Next.js → backend (evita CORS no browser)
    ├── components/
    │   ├── ThemeToggle.tsx        # toggle claro/escuro (localStorage)
    │   └── MobileNav.tsx         # menu hamburger responsivo (mobile)
    └── lib/
        ├── api.ts                # funções de fetch para o backend
        └── meditation.tsx        # parsing e renderização do texto
```

---

## Banco de dados

Tabela `meditacoes`:

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | integer PK | identificador |
| `data` | varchar(10) UNIQUE | data no formato `DD/MM/AAAA` |
| `titulo_raw` / `titulo` | text | título em espanhol — usado pelo toggle ES do frontend (raw HTML / normalizado) |
| `subtitulo_raw` / `subtitulo` | text | subtítulo em espanhol |
| `leitura_ref_raw` / `leitura_ref` | text | referência litúrgica em espanhol |
| `leitura_ref_pt` | text | referência litúrgica em português |
| `conteudo_i_raw` / `conteudo_i` | text | seção I em espanhol |
| `conteudo_ii_raw` / `conteudo_ii` | text | seção II em espanhol |
| `conteudo_iii_raw` / `conteudo_iii` | text | seção III em espanhol |
| `titulo_pt` | text | título em português |
| `subtitulo_pt` | text | subtítulo em português |
| `conteudo_i_pt` | text | seção I em português |
| `conteudo_ii_pt` | text | seção II em português |
| `conteudo_iii_pt` | text | seção III em português |
| `fonte_traducao` | varchar(50) | origem do conteúdo em português: `site_pt` (raspado direto, sem tradução), `openrouter` ou `deepl` (fallback traduzido) |
| `criado_em` | timestamptz | data de inserção |

> Os campos `*_raw` preservam o HTML original; os campos normalizados convertem `<em>`/`<i>` em marcadores `*texto*`, removem mojibake e limpam entidades HTML.
>
> No raro caso em que a raspagem em português funciona mas a raspagem em espanhol falha no mesmo dia, os campos em espanhol ficam como cópia do texto em português (o toggle ES do frontend mostraria português nesse dia específico).

---

## API REST

Base URL: `http://localhost:8000`

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| `GET` | `/meditacoes/hoje` | — | Meditação do dia atual (fuso: America/Sao_Paulo) |
| `GET` | `/meditacoes/por-data?data=DD/MM/AAAA` | — | Meditação por data específica |
| `GET` | `/meditacoes/?limit=20&offset=0` | — | Lista paginada de meditações |
| `POST` | `/meditacoes/raspar` | `X-API-Key` | Raspa e salva uma meditação (parâmetros abaixo) |
| `POST` | `/contato/` | — | Envia mensagem de contato por e-mail |

Documentação interativa disponível em `http://localhost:8000/docs`.

### Parâmetros de `/raspar`

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `force` | bool | `false` | Sobrescreve o registro se já existir |
| `source_url` | string | — (usa PT com fallback ES automático) | Força a raspagem de uma URL específica |
| `translate` | bool | inferido pela URL (só se `source_url` informado) | Válido apenas junto com `source_url`. Se omitido, é inferido automaticamente pela URL: URLs com `/pt/` não são traduzidas, as demais são tratadas como espanhol e traduzidas. Se `true`, força tradução via LLM/DeepL (assume-se fonte em espanhol). Se `false`, força salvar o conteúdo raspado direto como português, sem tradução |
| `pt_only` | bool | `false` | Válido apenas junto com `source_url`. Se `true`, atualiza somente os campos em português com o conteúdo raspado, **preservando o conteúdo em espanhol já salvo** para a data (se não existir registro para a data, cria um novo raspando a fonte em espanhol normalmente). Mutuamente exclusivo com `es_only` |
| `es_only` | bool | `false` | Válido apenas junto com `source_url`. Se `true`, atualiza somente os campos em espanhol com o conteúdo raspado, **preservando o conteúdo em português já salvo** para a data (se não existir registro para a data, cria um novo traduzindo o conteúdo raspado para português). Mutuamente exclusivo com `pt_only` |
| `date` | string `DD/MM/AAAA` | hoje (America/Sao_Paulo) | Data a ser gravada no banco |

Quando `source_url` não é informado, o serviço tenta primeiro `SCRAPE_SOURCE_URL_PT` (conteúdo já em português, sem tradução) e só recorre a `SCRAPE_SOURCE_URL` (espanhol) com tradução via LLM/DeepL se a raspagem em português falhar; nesse caso `translate` é ignorado.

Os parâmetros são independentes e opcionais. Exemplos:

```bash
# Raspagem normal do dia atual
curl -s -X POST "http://localhost:8000/meditacoes/raspar" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool

# Forçar nova raspagem do dia atual (sobrescreve)
curl -s -X POST "http://localhost:8000/meditacoes/raspar?force=true" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool

# Raspar de uma URL alternativa em espanhol com data específica (ex: diferença de fuso) — traduz por padrão
curl -s -X POST "http://localhost:8000/meditacoes/raspar?force=true&date=29/06/2026&source_url=https://hablarcondios.org/meditacion-dia-anterior/" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool

# Raspar de uma URL alternativa já em português, sem tradução (sobrescreve ES e PT com o mesmo conteúdo)
curl -s -X POST "http://localhost:8000/meditacoes/raspar?force=true&date=29/06/2026&source_url=https://hablarcondios.org/pt/meditacao-dia-anterior/&translate=false" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool

# Raspar de uma URL alternativa em português SÓ para a aba PT, preservando o conteúdo em espanhol já salvo
curl -s -X POST "http://localhost:8000/meditacoes/raspar?force=true&date=09/07/2026&source_url=https://hablarcondios.org/pt/meditacao-no-dia-anterior/&pt_only=true" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool

# Raspar de uma URL alternativa em espanhol SÓ para a aba ES, preservando o conteúdo em português já salvo
curl -s -X POST "http://localhost:8000/meditacoes/raspar?force=true&date=09/07/2026&source_url=https://hablarcondios.org/meditacion-dia-anterior/&es_only=true" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool
```

---

## Variáveis de ambiente

### Backend (`backend/.env`)

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `DATABASE_URL` | sim | — | URL de conexão PostgreSQL |
| `OPENROUTER_API_KEY` | não | — | Chave da API OpenRouter (tradução principal via LLM) |
| `LLM_MODEL` | não | `openai/gpt-5-mini` | Modelo usado pelo OpenRouter |
| `DEEPL_API_KEY` | não | — | Chave da API DeepL (fallback quando OpenRouter falha) |
| `SCRAPE_API_KEY` | sim | — | Chave secreta para o endpoint `/raspar` |
| `AMBIENTE` | não | `development` | Ambiente da aplicação |
| `SCRAPE_SOURCE_URL_PT` | não | `https://hablarcondios.org/pt/meditacao-diaria/` | URL primária, já em português (sem necessidade de tradução) |
| `SCRAPE_SOURCE_URL` | não | `https://hablarcondios.org/meditacion-diaria/` | URL de fallback em espanhol, usada com tradução via LLM/DeepL quando a raspagem em português falha |
| `SCRAPE_SCHEDULE_HOUR` | não | `0` | Hora da 1ª tentativa de raspagem (fuso configurado) |
| `SCRAPE_SCHEDULE_MINUTE` | não | `17` | Minuto da raspagem (repetido nas 3 tentativas) |
| `TIMEZONE` | não | `America/Sao_Paulo` | Fuso horário do scheduler |
| `CORS_ORIGINS` | não | `["http://localhost:3000"]` | Origens permitidas pelo CORS |
| `SMTP_HOST` | não | `smtp.gmail.com` | Servidor SMTP para envio de e-mail |
| `SMTP_PORT` | não | `587` | Porta SMTP (TLS) |
| `SMTP_USER` | sim | — | E-mail remetente (conta SMTP) |
| `SMTP_PASSWORD` | sim | — | Senha de app do e-mail remetente |
| `CONTACT_EMAIL` | sim | — | E-mail destinatário das mensagens de contato |

> Para Gmail, gere uma **senha de app** em: Conta Google → Segurança → Verificação em duas etapas → Senhas de app.

### Frontend (`frontend/.env.local`)

| Variável | Padrão | Descrição |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL base do backend |

---

## Execução com Docker (recomendado)

### 1. Configurar variáveis de ambiente

```bash
cp backend/.env.example backend/.env
# edite backend/.env com suas chaves
```

### 2. Subir todos os serviços

```bash
docker compose up --build
```

Serviços disponíveis:

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Docs interativos | http://localhost:8000/docs |

> O banco de dados usa um volume Docker nomeado (`postgres_data`), mantendo os dados entre reinicializações.

### 3. Popular o banco

A raspagem automática ocorre diariamente com até 3 tentativas: **00:17**, **03:17** e **06:17** (America/Sao_Paulo). Se a meditação já foi salva em uma tentativa anterior, as seguintes são ignoradas automaticamente.

Para popular manualmente:

```bash
curl -s -X POST "http://localhost:8000/meditacoes/raspar" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool
```

---

## Execução local sem Docker

### Backend

Requer Python 3.11+ e [`uv`](https://github.com/astral-sh/uv).

```bash
cd backend
uv sync
cp .env.example .env
# edite .env com suas chaves e a DATABASE_URL apontando para um PostgreSQL local
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

Requer Node.js 18+.

```bash
cd frontend
npm install
npm run dev
```

---

## Pipeline de conteúdo

```
hablarcondios.org/pt/meditacao-diaria/ (HTML, fonte primária)
    │
    ▼ BeautifulSoup + text_normalizer
Extração e limpeza dos campos: título, subtítulo, referência litúrgica, seções I/II/III
(a descrição de cada seção, marcada no site com um traço — "—", "–" ou "-" —, é detectada
 e embutida como "— descrição\n\n corpo" no início de conteudo_i/ii/iii)
    │
    ├─► sucesso: campos *_pt = texto em português direto (fonte_traducao = "site_pt")
    │
    └─► também raspa hablarcondios.org/meditacion-diaria/ (BeautifulSoup + text_normalizer)
            só para preencher campos *_raw / normalizados em espanhol (sem tradução),
            usados pelo toggle ES do frontend
            (se essa raspagem falhar, os campos em espanhol viram cópia do texto em português)

    ── se a raspagem em português falhar (rede, HTTP, estrutura inesperada) ──

hablarcondios.org/meditacion-diaria/ (HTML, fallback em espanhol)
    │
    ▼ BeautifulSoup + text_normalizer (mesmo processo acima)
    │
    ├─► Salvo como campo *_raw / normalizado em espanhol
    │
    ▼ OpenRouter (LLM especializado em linguagem sacra) / DeepL (fallback)
Tradução ES → PT-BR preservando marcadores *texto*
    │
    ▼ PostgreSQL
Campos *_pt armazenam a versão em português (fonte_traducao = "openrouter" ou "deepl")
    │
    ▼ Frontend (Next.js SSR)
stripItalicMarkers()         remove asteriscos do subtítulo geral (já exibido em itálico via CSS)
parseItalicFromText()        converte *texto* → <em> no título, nas descrições de seção e no corpo
renderTextWithReferences()   aplica parseItalicFromText() e vincula [N] às referências como âncoras bidirecionais
splitSectionSubtitle()       extrai a descrição embutida ("— texto") no início de cada seção I/II/III
splitReflectionAndCitations() separa corpo da meditação, citações e apêndice — reconhece tanto o
                              formato da pipeline ES+LLM ("1 texto — 2 texto") quanto o formato nativo
                              do site em português ("(1) texto; (2) texto")
```

---

## Scripts utilitários

### Editar uma meditação manualmente

```bash
cd backend
uv run python scripts/editar_meditacao.py DD/MM/AAAA
```

Abre um editor interativo com todos os campos da meditação para correção manual.

---

## Funcionalidades do frontend

| Página | Rota | Descrição |
|---|---|---|
| Meditação do dia | `/` | Exibe a meditação atual com índice de seções navegável |
| Arquivo | `/arquivo` | Navegação por data com lista lateral paginada |
| Sobre | `/sobre` | Apresentação do projeto e atribuição de direitos |
| Contato | `/contato` | Formulário de contato com envio de e-mail |

**Recursos da interface:**
- Modo claro / escuro com persistência em `localStorage` e respeito a `prefers-color-scheme`
- Imagem de fundo sacra com cards translúcidos
- Fonte manuscrita (Dancing Script) no logotipo
- Menu hamburger responsivo para dispositivos móveis
- Índice de seções (I, II, III) com hiperlinks âncora internos
- Links bidirecionais entre citações no texto e referências no rodapé
- `scroll-margin-top` em todas as âncoras para compensar o navbar fixo
- Texto em itálico preservado da obra original
- Suporte a português e espanhol (toggle por idioma)
- Tipografia serifada com texto justificado
- Formulário de contato com feedback de sucesso/erro e aviso de uso de dados (LGPD)
- Proxy via Next.js API route (`/api/contato`) para chamadas do browser ao backend
