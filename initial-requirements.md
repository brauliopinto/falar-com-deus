# Requirements — Meditação Diária 🙏

Documento de requisitos técnicos e funcionais do projeto **Meditação Diária**,
uma aplicação que realiza raspagem diária do site [Hablar con Dios](https://hablarcondios.org/meditacion-diaria/),
traduz o conteúdo para o português e o exibe em uma página web personalizada.

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Requisitos Funcionais](#2-requisitos-funcionais)
3. [Requisitos Não Funcionais](#3-requisitos-não-funcionais)
4. [Stack Tecnológica](#4-stack-tecnológica)
5. [Modelo de Dados](#5-modelo-de-dados)
6. [Endpoints da API](#6-endpoints-da-api)
7. [Pré-requisitos de Ambiente](#7-pré-requisitos-de-ambiente)
8. [Instalação](#8-instalação)
9. [Variáveis de Ambiente](#9-variáveis-de-ambiente)
10. [Hospedagem](#10-hospedagem)

---

## 1. Visão Geral

| Item        | Detalhe                                              |
|-------------|------------------------------------------------------|
| **Projeto** | Meditação Diária                                     |
| **Origem**  | hablarcondios.org/meditacion-diaria                  |
| **Idioma original** | Espanhol                                     |
| **Idioma exibido**  | Português (BR)                               |
| **Frequência** | Raspagem automática 1x por dia                    |
| **Armazenamento** | PostgreSQL — 1 registro por data (dd/mm/aaaa) |

---

## 2. Requisitos Funcionais

| ID   | Requisito                                                                 |
|------|---------------------------------------------------------------------------|
| RF01 | Acessar diariamente a página de meditação e extrair seu conteúdo          |
| RF02 | Associar cada meditação à data do dia no formato `dd/mm/aaaa`             |
| RF03 | Extrair os campos: título, subtítulo, referência bíblica, seções I/II/III e reflexão final |
| RF04 | Traduzir todos os campos de Espanhol para Português via DeepL API         |
| RF05 | Gravar o conteúdo original (ES) e traduzido (PT) no banco de dados        |
| RF06 | Não duplicar registros — ignorar raspagem se a data já existir no banco   |
| RF07 | Expor os dados via API REST (FastAPI)                                     |
| RF08 | Exibir a meditação do dia atual em uma página web estilizada              |
| RF09 | Permitir consulta de meditações por data específica                       |
| RF10 | Permitir disparo manual da raspagem via endpoint protegido                |

---

## 3. Requisitos Não Funcionais

| ID    | Requisito                                                              |
|-------|------------------------------------------------------------------------|
| RNF01 | A raspagem deve ser agendada para executar diariamente às **06:00**    |
| RNF02 | O sistema deve funcionar em ambiente de deploy externo (não local)     |
| RNF03 | As credenciais sensíveis devem ser armazenadas em variáveis de ambiente |
| RNF04 | O banco de dados deve ser PostgreSQL 16+                               |
| RNF05 | O frontend deve ser responsivo (mobile-friendly)                       |
| RNF06 | A API deve retornar respostas em formato JSON                          |
| RNF07 | O custo de hospedagem deve ser o menor possível                        |
| RNF08 | O sistema deve registrar logs de erro em caso de falha na raspagem     |

---

## 4. Stack Tecnológica

### Backend
| Tecnologia       | Versão   | Finalidade                        |
|------------------|----------|-----------------------------------|
| Python           | 3.11+    | Linguagem principal               |
| FastAPI          | latest   | Framework da API REST             |
| Uvicorn          | latest   | Servidor ASGI                     |
| SQLAlchemy       | latest   | ORM para o banco de dados         |
| Alembic          | latest   | Migrations do banco               |
| psycopg2-binary  | latest   | Driver PostgreSQL                 |
| BeautifulSoup4   | latest   | Parsing do HTML raspado           |
| Requests         | latest   | Requisições HTTP para o scraping  |
| APScheduler      | latest   | Agendamento da tarefa diária      |
| DeepL            | latest   | Tradução ES → PT via API          |
| python-dotenv    | latest   | Leitura das variáveis de ambiente |
| Pydantic         | latest   | Validação e schemas da API        |

### Frontend
| Tecnologia   | Versão   | Finalidade                        |
|--------------|----------|-----------------------------------|
| Next.js      | 14+      | Framework React com SSR           |
| TypeScript   | latest   | Tipagem estática                  |
| Tailwind CSS | latest   | Estilização utilitária            |

### Banco de Dados
| Tecnologia  | Versão | Finalidade           |
|-------------|--------|----------------------|
| PostgreSQL  | 16+    | Banco de dados principal |

---

## 5. Modelo de Dados

Tabela: `meditacoes`

| Coluna           | Tipo          | Descrição                          |
|------------------|---------------|------------------------------------|
| `id`             | SERIAL PK     | Identificador único                |
| `data`           | VARCHAR(10)   | Data no formato `dd/mm/aaaa` (UNIQUE) |
| `titulo`         | TEXT          | Título original (ES)               |
| `subtitulo`      | TEXT          | Subtítulo original (ES)            |
| `leitura_ref`    | TEXT          | Referência bíblica (ex: Mt 16, 13-19) |
| `conteudo_i`     | TEXT          | Seção I em Espanhol                |
| `conteudo_ii`    | TEXT          | Seção II em Espanhol               |
| `conteudo_iii`   | TEXT          | Seção III em Espanhol              |
| `reflexao`       | TEXT          | Reflexão final em Espanhol         |
| `titulo_pt`      | TEXT          | Título traduzido (PT)              |
| `subtitulo_pt`   | TEXT          | Subtítulo traduzido (PT)           |
| `conteudo_i_pt`  | TEXT          | Seção I em Português               |
| `conteudo_ii_pt` | TEXT          | Seção II em Português              |
| `conteudo_iii_pt`| TEXT          | Seção III em Português             |
| `reflexao_pt`    | TEXT          | Reflexão final em Português        |
| `fonte_traducao` | VARCHAR(50)   | Ferramenta usada (`deepl`)         |
| `criado_em`      | TIMESTAMP     | Data/hora de criação do registro   |

---

## 6. Endpoints da API

| Método | Rota                      | Descrição                                 | Autenticação |
|--------|---------------------------|-------------------------------------------|--------------|
| GET    | `/meditacoes/hoje`        | Retorna a meditação do dia atual          | Não          |
| GET    | `/meditacoes/{data}`      | Retorna meditação de uma data específica  | Não          |
| GET    | `/meditacoes/`            | Lista todas as meditações (paginado)      | Não          |
| POST   | `/meditacoes/raspar`      | Dispara raspagem manualmente              | Sim (API Key)|
| POST   | `/meditacoes/raspar/dia-anterior` | Dispara raspagem da meditação do dia anterior | Sim (API Key)|

---

## 7. Pré-requisitos de Ambiente

- [ ] Python `3.11+` instalado → `python --version`
- [ ] Node.js `20.x LTS` instalado → `node --version`
- [ ] PostgreSQL `16+` instalado e rodando → `pg_isready`
- [ ] Git instalado e configurado → `git --version`
- [ ] Conta criada no [DeepL](https://www.deepl.com/pro#developer) com API Key gerada
- [ ] Conta no [Railway](https://railway.app) para deploy do backend
- [ ] Conta no [Vercel](https://vercel.com) para deploy do frontend

### Extensões recomendadas no VSCode

| Extensão                   | ID                                      |
|----------------------------|-----------------------------------------|
| Python                     | `ms-python.python`                      |
| Pylance                    | `ms-python.vscode-pylance`              |
| ESLint                     | `dbaeumer.vscode-eslint`                |
| Prettier                   | `esbenp.prettier-vscode`                |
| Tailwind CSS IntelliSense  | `bradlc.vscode-tailwindcss`             |
| PostgreSQL (by cweijan)    | `cweijan.vscode-postgresql-client2`     |
| Thunder Client             | `rangav.vscode-thunder-client`          |
| GitLens                    | `eamodio.gitlens`                       |
| DotENV                     | `mikestead.dotenv`                      |

---

## 8. Instalação

### 1. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/meditacao-diaria.git
cd meditacao-diaria
```

### 2. Configurar o backend
```bash
cd backend
uv sync
```

### 3. Configurar o banco de dados local
```sql
CREATE DATABASE meditacoes;
CREATE USER meditacao_user WITH PASSWORD 'suasenha123';
GRANT ALL PRIVILEGES ON DATABASE meditacoes TO meditacao_user;
```

### 4. Configurar o frontend
```bash
cd frontend
npm install
```

### 5. Rodar localmente

**Terminal 1 — Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

| Serviço      | URL                          |
|--------------|------------------------------|
| Frontend     | http://localhost:3000        |
| API          | http://localhost:8000        |
| Docs da API  | http://localhost:8000/docs   |

---

## 9. Variáveis de Ambiente

### `backend/.env`
```env
DATABASE_URL=postgresql://meditacao_user:suasenha123@localhost:5432/meditacoes
DEEPL_API_KEY=cole-sua-chave-aqui
SECRET_KEY=qualquer-string-segura-aqui
AMBIENTE=development
```

### `frontend/.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> ⚠️ **Nunca suba arquivos `.env` para o repositório.**
> Certifique-se de que estão listados no `.gitignore`.

---

## 10. Hospedagem

| Serviço   | Plataforma | Custo estimado         |
|-----------|------------|------------------------|
| Backend   | Railway    | ~$5/mês (ou gratuito com crédito) |
| Banco     | Railway    | Incluso no plano       |
| Frontend  | Vercel     | Gratuito               |

---

*Documento gerado em: 27/06/2026*