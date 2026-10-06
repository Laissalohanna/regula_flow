from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from regulaflow import __version__
from regulaflow.application.clock import Clock, SystemClock
from regulaflow.application.errors import ProcessingFailureError
from regulaflow.application.service import BatchService, Evaluator
from regulaflow.application.store import BatchStore
from regulaflow.domain.errors import (
    BatchNotFoundError,
    DuplicateBatchError,
    NotReprocessableError,
)
from regulaflow.infrastructure.db import create_session_factory
from regulaflow.infrastructure.repository import SqlAlchemyBatchStore
from regulaflow.infrastructure.settings import Settings
from regulaflow.interfaces.http import create_router


def create_app(
    database_url: str | None = None,
    store: BatchStore | None = None,
    clock: Clock | None = None,
    evaluator: Evaluator | None = None,
) -> FastAPI:
    if store is None:
        settings = Settings()
        url = database_url or settings.database_url
        store = SqlAlchemyBatchStore(create_session_factory(url))
    app = FastAPI(title="RegulaFlow", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Settings().cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(
        create_router(BatchService(store, clock or SystemClock(), evaluator))
    )
    _register_errors(app)
    return app


def _register_errors(app: FastAPI) -> None:
    @app.exception_handler(DuplicateBatchError)
    def duplicate_batch(_request: object, exc: DuplicateBatchError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(BatchNotFoundError)
    def missing_batch(_request: object, exc: BatchNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(NotReprocessableError)
    def not_reprocessable(
        _request: object,
        exc: NotReprocessableError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ProcessingFailureError)
    def processing_failure(
        _request: object,
        exc: ProcessingFailureError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "batch_id": str(exc.batch_id)},
        )
