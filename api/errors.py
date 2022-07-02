from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response

from api.dto import ErrorResponseDto


class NotFoundError(RuntimeError):
    pass


class InvalidCronExpressionError(RuntimeError):
    pass


class RunAssignmentFailed(RuntimeError):
    pass


class RunCompletionFailed(RuntimeError):
    pass


def default_error_response(status: int, ex: Exception) -> Response:
    return JSONResponse(status_code=status, content=jsonable_encoder(ErrorResponseDto(detail=str(ex))))


def register_error_handlers(app: FastAPI):
    @app.exception_handler(NotFoundError)
    async def handle_not_found_error(request: Request, ex: NotFoundError) -> Response:
        return default_error_response(status.HTTP_404_NOT_FOUND, ex)

    @app.exception_handler(InvalidCronExpressionError)
    async def handle_invalid_cron_expression_error(request: Request, ex: InvalidCronExpressionError) -> Response:
        return default_error_response(status.HTTP_400_BAD_REQUEST, ex)

    @app.exception_handler(RunAssignmentFailed)
    async def handle_run_assignment_failed(request: Request, ex: RunAssignmentFailed) -> Response:
        return default_error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, ex)

    @app.exception_handler(RunCompletionFailed)
    async def handle_run_completion_failed(request: Request, ex: RunCompletionFailed) -> Response:
        return default_error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, ex)
