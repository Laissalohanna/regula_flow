# RegulaFlow

Plataforma de processamento e validação de operações financeiras.

**Versão:** 1.0 · **Status:** Em desenvolvimento · **Tipo:** Projeto de portfólio

> Dados e regras fictícios, para fins educacionais e de demonstração técnica. Este projeto não representa uma implementação oficial de nenhum leiaute ou norma do Banco Central.

O RegulaFlow recebe lotes de operações, valida estrutura e regras de negócio, registra inconsistências e acompanha cada execução até o resultado. A validação acontece antes de os dados avançarem no fluxo operacional.

A especificação completa está em [docs/produto.md](docs/produto.md).

## Stack

| Camada | Tecnologia |
| --- | --- |
| Linguagem | Python 3.12 |
| API | FastAPI |
| Validação | Pydantic |
| ORM | SQLAlchemy |
| Banco | PostgreSQL (SQLite no desenvolvimento local) |
| Migração | Alembic |
| Painel | React, TypeScript e Vite |
| Testes | Pytest |
| Qualidade | Ruff + MyPy |
| Containerização | Docker |
| Documentação da API | OpenAPI / Swagger |

## O que existe hoje

- API FastAPI e documentação Swagger
- PostgreSQL, com SQLite para rodar local
- Cadastro de lotes e de operações, com tipo de movimento
- Validações e registro de erros
- Consulta de processamento, métricas e painel
- Reprocessamento
- Painel web
- Testes automatizados
- Docker (API e PostgreSQL)

Na sequência: Celery, Redis, retry, idempotência, observabilidade e CI/CD.

## Tipos de movimento

Cada operação informa um tipo. Se o campo vier omitido, o padrão é aquisição. A revisão Alembic `0002_movement` cria a coluna `movement_type` em `operations` (`alembic upgrade head` aplica `0001_initial` e esta revisão).

| Código | Rótulo |
| --- | --- |
| `ACQUISITION` | Aquisição |
| `SETTLEMENT` | Liquidação |
| `TRANSFER` | Transferência |
| `REDEMPTION` | Resgate |
| `REVERSAL` | Estorno |

## Telas

| Rota | Conteúdo |
| --- | --- |
| `/` | Painel: totais e gráficos de performance, tipo de arquivo, etapa de validação e tipo de movimento |
| `/lotes` | Lista de lotes |
| `/lotes/novo` | Cadastro de um lote |
| `/lotes/:id` | Operações, inconsistências, histórico e reprocessamento |
| `/inconsistencias` | Consulta filtrada da última execução de cada lote |
| `/regras` | Catálogo das regras aplicadas |

No detalhe do lote dá para baixar o CSV das operações com os erros da última execução, gerar o relatório em PDF e abrir o resumo no WhatsApp. O QR Code da mesma tela leva a esse envio. A exportação CSV da tela de inconsistências sai do filtro atual. PDF, QR Code e os dois CSVs são montados no navegador.

## Endpoints

| Método | Caminho | Uso |
| --- | --- | --- |
| `GET` | `/health` | Saúde da API e do banco |
| `POST` | `/api/lotes` | Recebe um lote |
| `GET` | `/api/lotes` | Lista os lotes |
| `GET` | `/api/lotes/{id}` | Detalhe do lote |
| `POST` | `/api/lotes/{id}/reprocessamentos` | Reprocessa o lote |
| `GET` | `/api/metricas` | Totais e taxas |
| `GET` | `/api/painel` | Dados dos gráficos do painel |
| `GET` | `/api/inconsistencias` | Consulta por `lote`, `operacao`, `regra`, `severidade`, `desde` e `ate` |

`GET /api/painel` devolve taxas, tempo médio, reprocessamentos, falhas, tipos de arquivo, etapas e a contagem de cada tipo de movimento.

## Executar a API

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
$env:DATABASE_URL = "sqlite+pysqlite:///./regulaflow.db"
$env:SEED_DEMO = "true"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe regulaflow.composition.factory:create_app --factory --reload
```

A documentação interativa fica em `http://localhost:8000/docs`.

`SEED_DEMO=true` grava uma amostra fictícia de outubro de 2026 quando o banco ainda não tem lotes. Sem a variável, a API sobe vazia.

O painel sobe em outra pasta e encaminha `/api` e `/health` para a API em `http://127.0.0.1:8000`:

```powershell
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

Com Docker, a API sobe junto com o PostgreSQL:

```powershell
docker compose up --build
```
