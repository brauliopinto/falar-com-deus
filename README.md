# Falar com Deus

Aplicação web para leitura diária das meditações de *Hablar con Dios*, de **Francisco Fernández-Carvajal** (Ediciones Palabra), traduzidas automaticamente para o português do Brasil.

O conteúdo é obtido diariamente do portal [hablarcondios.org](https://hablarcondios.org), traduzido via **DeepL** e servido em uma interface limpa com suporte a modo noturno.

> **Aviso de direitos:** todo o conteúdo das meditações é propriedade intelectual de Francisco Fernández-Carvajal e Ediciones Palabra, S.A. Este projeto é pessoal, sem fins comerciais e sem vínculo oficial com os titulares dos direitos.

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLAlchemy · Alembic · APScheduler |
| Scraping | BeautifulSoup4 · Requests |
| Tradução | DeepL API |
| Banco de dados | PostgreSQL 16 |
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS |
| Infraestrutura | Docker · Docker Compose |

---

## Arquitetura

```
hablarcondios.org
      │
      ▼ HTTP scrape (diário, 06:00 BRT)
┌─────────────┐     DeepL API      ┌──────────────┐
│   Scraper   │ ─────────────────► │  Translator  │
└─────────────┘                    └──────────────┘
      │ texto normalizado + traduzido
      ▼
┌─────────────────┐
│   PostgreSQL    │  tabela: meditacoes
└─────────────────┘
      │ REST API
      ▼
┌─────────────────┐
│  FastAPI (8000) │  /meditacoes/hoje · /meditacoes/por-data · /meditacoes/
└─────────────────┘
      │ fetch (SSR)
      ▼
┌─────────────────┐
│  Next.js (3000) │  / · /arquivo · /sobre
└─────────────────┘
```

---

## Estrutura do projeto

```
falar-com-deus/
├── docker-compose.yml
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
│       │   └── meditacao.py      # schemas Pydantic (request/response)
│       ├── api/routes/
│       │   └── meditacoes.py     # endpoints REST
│       └── services/
│           ├── scraper.py        # raspagem HTML + parsing
│           ├── text_normalizer.py # limpeza de mojibake, HTML entities, unicode
│           ├── translator.py     # integração DeepL
│           ├── meditation_service.py # orquestração (scrape → traduz → persiste)
│           └── scheduler.py      # APScheduler — job diário automático
└── frontend/
    ├── Dockerfile
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── app/
    │   ├── layout.tsx            # navbar + ThemeToggle + script anti-flash
    │   ├── globals.css
    │   ├── page.tsx              # meditação do dia
    │   ├── arquivo/page.tsx      # arquivo com navegação por data
    │   └── sobre/page.tsx        # apresentação e direitos autorais
    ├── components/
    │   └── ThemeToggle.tsx       # toggle claro/escuro (localStorage)
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
| `titulo_raw` / `titulo` | text | título em espanhol (raw HTML / normalizado) |
| `subtitulo_raw` / `subtitulo` | text | subtítulo em espanhol |
| `leitura_ref_raw` / `leitura_ref` | text | referência litúrgica em espanhol |
| `leitura_ref_pt` | text | referência litúrgica em português |
| `conteudo_i_raw` / `conteudo_i` | text | seção I em espanhol |
| `conteudo_ii_raw` / `conteudo_ii` | text | seção II em espanhol |
| `conteudo_iii_raw` / `conteudo_iii` | text | seção III em espanhol |
| `titulo_pt` | text | título traduzido |
| `subtitulo_pt` | text | subtítulo traduzido |
| `conteudo_i_pt` | text | seção I traduzida |
| `conteudo_ii_pt` | text | seção II traduzida |
| `conteudo_iii_pt` | text | seção III traduzida |
| `fonte_traducao` | varchar(50) | fonte da tradução (ex: `deepl`) |
| `criado_em` | timestamptz | data de inserção |

> Os campos `*_raw` preservam o HTML original; os campos normalizados convertem `<em>`/`<i>` em marcadores `*texto*`, removem mojibake e limpam entidades HTML.

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
| `source_url` | string | URL padrão do site espanhol | URL de onde raspar o HTML |
| `date` | string `DD/MM/AAAA` | hoje (America/Sao_Paulo) | Data a ser gravada no banco |

Os três parâmetros são independentes e opcionais. Exemplos:

```bash
# Raspagem normal do dia atual
curl -s -X POST "http://localhost:8000/meditacoes/raspar" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool

# Forçar nova raspagem do dia atual (sobrescreve)
curl -s -X POST "http://localhost:8000/meditacoes/raspar?force=true" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool

# Raspar de uma URL alternativa com data específica (ex: diferença de fuso)
curl -s -X POST "http://localhost:8000/meditacoes/raspar?force=true&date=29/06/2026&source_url=https://hablarcondios.org/meditacion-dia-anterior/" \
  -H "X-API-Key: SUA_SCRAPE_API_KEY" | python3 -m json.tool
```

---

## Variáveis de ambiente

### Backend (`backend/.env`)

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `DATABASE_URL` | sim | — | URL de conexão PostgreSQL |
| `DEEPL_API_KEY` | sim | — | Chave da API DeepL |
| `SCRAPE_API_KEY` | sim | — | Chave secreta para o endpoint `/raspar` |
| `AMBIENTE` | não | `development` | Ambiente da aplicação |
| `SCRAPE_SOURCE_URL` | não | `https://hablarcondios.org/meditacion-diaria/` | URL de origem do conteúdo |
| `SCRAPE_SCHEDULE_HOUR` | não | `6` | Hora do job automático (fuso configurado) |
| `SCRAPE_SCHEDULE_MINUTE` | não | `0` | Minuto do job automático |
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

A raspagem automática ocorre diariamente às 06:00 (America/Sao_Paulo). Para popular manualmente:

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
cp .env.local.example .env.local   # se existir, ou crie manualmente
npm install
npm run dev
```

---

## Pipeline de conteúdo

```
hablarcondios.org (HTML)
    │
    ▼ BeautifulSoup
Extração dos campos: título, subtítulo, referência litúrgica, seções I/II/III
    │
    ▼ text_normalizer
Limpeza: remoção de mojibake, entidades HTML, normalização unicode,
conversão <em>/<i> → *texto* (marcador de itálico portátil)
    │
    ├─► Salvo como campo *_raw (HTML original)
    └─► Salvo como campo normalizado em espanhol
    │
    ▼ DeepL API
Tradução ES → PT-BR preservando marcadores *texto*
    │
    ▼ PostgreSQL
Campos *_pt armazenam a versão em português
    │
    ▼ Frontend (Next.js SSR)
parseItalicFromText() converte *texto* → <em>
renderTextWithReferences() vincula [N] às referências como âncoras
splitReflectionAndCitations() separa corpo da meditação, citações e apêndice
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
- Índice de seções (I, II, III) com hiperlinks âncora internos
- Citações bibliográficas com links âncora para a seção de referências
- Texto em itálico preservado da obra original
- Suporte a português e espanhol (toggle por idioma)
- Tipografia serifada com texto justificado
- Formulário de contato com feedback de sucesso/erro e proxy via Next.js API route
