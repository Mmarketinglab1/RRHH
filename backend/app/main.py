from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.middleware import TenantContextMiddleware
from app.api.routes import ai, auth, competencies, evaluations, participants, results, surveys
from app.core.config import settings
from app.core.rate_limit import limiter

app = FastAPI(title="Evaluation 360 AI SaaS", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ],
    allow_origin_regex=r"https://rrhh-web-[a-z0-9-]+\.run\.app|https://rrhh-web-[a-z0-9-]+-[a-z]+\.a\.run\.app|https://rrhh-web-[0-9]+\.us-central1\.run\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/cors")
def debug_cors() -> dict[str, str]:
    return {"status": "ok", "cors_origins": settings.cors_origins}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
app.include_router(competencies.router, prefix="/evaluations", tags=["competencies"])
app.include_router(participants.router, prefix="/evaluations", tags=["participants"])
app.include_router(surveys.router, prefix="/surveys", tags=["surveys"])
app.include_router(results.router, prefix="/evaluations", tags=["results"])
app.include_router(ai.router, prefix="/evaluations", tags=["ai"])
