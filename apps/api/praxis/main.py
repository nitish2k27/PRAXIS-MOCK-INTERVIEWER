"""FastAPI app entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from praxis.auth import router as auth_router
from praxis.config import settings
from praxis.routes.sessions import router as sessions_router
from praxis.routes.uploads import router as uploads_router

app = FastAPI(title="praxis-api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# SessionMiddleware holds Authlib OAuth state across the redirect dance.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=settings.cookie_secure,
)

app.include_router(auth_router)
app.include_router(uploads_router)
app.include_router(sessions_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
