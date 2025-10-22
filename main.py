"""
FastAPI application entry point for the string analytics service.
"""

from __future__ import annotations

from fastapi import FastAPI

from api import router

app = FastAPI(
    title="String Analytics Service",
    description="Analyze and manage strings with computed metadata.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/", tags=["health"])
def healthcheck() -> dict[str, str]:
    """Simple health endpoint to confirm the API is running."""
    return {"status": "ok"}
