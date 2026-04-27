import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, dashboard, users
from app.api.routes.ai_usage import integration_router as ai_integration_router
from app.api.routes.ai_usage import router as ai_usage_router
from app.api.routes.tts_usage import integration_router as tts_integration_router
from app.api.routes.tts_usage import router as tts_usage_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.bootstrap import ensure_initial_admin, init_db


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Range"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()
        with SessionLocal() as db:
            ensure_initial_admin(db)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(ai_usage_router, prefix=settings.api_prefix)
    app.include_router(tts_usage_router, prefix=settings.api_prefix)
    app.include_router(dashboard.router, prefix=settings.api_prefix)
    app.include_router(ai_integration_router, prefix=settings.api_prefix)
    app.include_router(tts_integration_router, prefix=settings.api_prefix)
    return app


app = create_app()


def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8100, reload=True)


if __name__ == "__main__":
    main()
