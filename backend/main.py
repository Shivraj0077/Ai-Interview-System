"""
API server.

    uvicorn main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.interviews import router as interviews_router
from config import settings
from errors import ServiceError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("api")

app = FastAPI(title="AI Technical Interviewer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _error(status: int, code: str, message: str, retryable: bool = False) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "retryable": retryable}})


@app.exception_handler(ServiceError)
async def service_error(_: Request, exc: ServiceError):
    return _error(exc.status_code, exc.code, exc.message, exc.retryable)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:])
    message = first.get("msg", "Invalid request").removeprefix("Value error, ")
    return _error(422, "invalid_request", f"{field}: {message}" if field else message)


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _error(500, "internal_error", "Something went wrong on our side. Please try again.", True)


app.include_router(interviews_router)
