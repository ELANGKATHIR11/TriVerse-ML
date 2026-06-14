"""
error_manager.py — TriVerse AI Global Error Handler

Provides:
  - GlobalErrorHandler: FastAPI exception handler middleware
  - structured JSON error envelopes for all unhandled exceptions
  - per-request correlation IDs for tracing
  - crash log rotation under logs/crashes/
"""

from __future__ import annotations

import logging
import os
import traceback
import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# ── Crash log directory ───────────────────────────────────────────────────────

_LOG_DIR = Path(__file__).resolve().parents[3] / "logs" / "crashes"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _write_crash_log(correlation_id: str, request: Request, exc: Exception) -> Path:
    """Persist a crash report to disk for offline diagnostics."""
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    log_path = _LOG_DIR / f"{ts}_{correlation_id[:8]}.txt"
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"TriVerse AI Crash Report\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"Timestamp       : {datetime.now(UTC).isoformat()}\n")
            f.write(f"Correlation ID  : {correlation_id}\n")
            f.write(f"Method          : {request.method}\n")
            f.write(f"URL             : {request.url}\n")
            f.write(f"Client          : {request.client}\n")
            f.write(f"\nException Type  : {type(exc).__name__}\n")
            f.write(f"Exception Msg   : {exc}\n")
            f.write(f"\nTraceback:\n")
            f.write(traceback.format_exc())
    except Exception as write_err:
        logger.warning("[ErrorManager] Failed to write crash log: %s", write_err)
    return log_path


def _build_error_response(
    correlation_id: str,
    status_code: int,
    error_type: str,
    message: str,
    detail: Any = None,
) -> dict[str, Any]:
    return {
        "error": True,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "status_code": status_code,
        "error_type": error_type,
        "message": message,
        "detail": detail,
        "support": "Check logs/crashes/ for full traceback.",
    }


# ── Request correlation middleware ────────────────────────────────────────────

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Correlation-ID header into every request/response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = cid

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response


# ── Global exception handler ──────────────────────────────────────────────────

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches any unhandled exception, logs it, writes a crash report,
    and returns a structured JSON error envelope.
    """
    cid = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    logger.exception(
        "[ErrorManager] Unhandled exception [%s] %s %s: %s",
        cid,
        request.method,
        request.url,
        exc,
    )

    crash_path = _write_crash_log(cid, request, exc)
    logger.info("[ErrorManager] Crash report saved: %s", crash_path)

    body = _build_error_response(
        correlation_id=cid,
        status_code=500,
        error_type=type(exc).__name__,
        message="An unexpected internal server error occurred.",
        detail=str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None,
    )
    return JSONResponse(status_code=500, content=body)


# ── HTTPException override ────────────────────────────────────────────────────

from fastapi.exceptions import HTTPException, RequestValidationError


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    cid = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    body = _build_error_response(
        correlation_id=cid,
        status_code=exc.status_code,
        error_type="HTTPException",
        message=exc.detail,
    )
    return JSONResponse(status_code=exc.status_code, content=body)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    cid = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    body = _build_error_response(
        correlation_id=cid,
        status_code=422,
        error_type="ValidationError",
        message="Request validation failed.",
        detail=exc.errors(),
    )
    return JSONResponse(status_code=422, content=body)


# ── Registration helper ───────────────────────────────────────────────────────

def register_error_handlers(app: FastAPI) -> None:
    """
    Wire all error handlers and middleware into the FastAPI app.
    Call this once in main.py after app creation.
    """
    app.add_middleware(CorrelationIDMiddleware)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    logger.info("[ErrorManager] Global error handlers registered.")
