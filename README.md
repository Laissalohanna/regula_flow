# RegulaFlow

Plataforma de processamento e validação de operações financeiras.

**Versão:** 1.0 · **Status:** Em desenvolvimento · **Tipo:** Projeto de portfólio

> Dados e regras fictícios, para fins educacionais e de demonstração técnica. Este projeto não representa uma implementação oficial de nenhum leiaute ou norma do Banco Central.

O RegulaFlow recebe lotes de operações, valida estrutura e regras de negócio, registra inconsistências e acompanha cada execução até o resultado. A validação acontece antes de os dados avançarem no fluxo operacional.

A especificação completa está em [docs/produto.md](docs/produto.md).

## Stack

| Camada | Tecnologia |
| --- | --- |
| Linguagem | Python |
| API | FastAPI |
| Validação | Pydantic |
| ORM | SQLAlchemy |
| Banco | PostgreSQL |
| Migração | Alembic |
| Mensageria | Redis |
| Jobs | Celery |
| Testes | Pytest |
| Qualidade | Ruff + MyPy |
| Containerização | Docker |
| Observabilidade | Prometheus + Grafana |
| CI/CD | GitHub Actions |
| Documentação da API | OpenAPI / Swagger |

## MVP

- API FastAPI e documentação Swagger
- PostgreSQL
- Cadastro de lotes e de operações
- Validações e registro de erros
- Consulta de processamento
- Testes automatizados
- Docker

Na sequência: Celery, Redis, retry, idempotência, observabilidade e CI/CD.

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

O painel sobe em outra pasta:

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
