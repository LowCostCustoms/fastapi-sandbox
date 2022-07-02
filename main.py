from fastapi import FastAPI

from api.errors import register_error_handlers
from api.middleware import register_middleware
from api.router import router

app = FastAPI()
app.include_router(router)

register_error_handlers(app)
register_middleware(app)
