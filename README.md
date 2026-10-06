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
