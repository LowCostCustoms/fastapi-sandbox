from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from api.db import SessionLocal
from api.db import override_session


def register_middleware(app: FastAPI):
    @app.middleware("http")
    async def configure_session(request: Request, next) -> Response:
        async with SessionLocal() as session:
            async with override_session(session):
                return await next(request)
