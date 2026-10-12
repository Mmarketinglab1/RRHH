from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.middleware import TenantContextMiddleware
from app.api.routes import ai, auth, competencies, competency_bank, evaluations, participants, results, surveys
from app.core.config import settings
from app.core.rate_limit import limiter

from sqlalchemy import text
from app.db.session import engine

def run_auto_migrations():
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS assessment_type VARCHAR(60) DEFAULT 'individual_contributor';"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS client_logo_url TEXT;"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE evaluations ALTER COLUMN client_logo_url TYPE TEXT;"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS consultant_logo_url TEXT;"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE evaluations ALTER COLUMN consultant_logo_url TYPE TEXT;"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS report_config JSONB DEFAULT '{}'::jsonb;"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS scale_type VARCHAR(50) DEFAULT 'numeric_1_10';"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS score_thresholds JSONB DEFAULT '{\"high\": 8.5, \"medium\": 7.0}'::jsonb;"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE participants ADD COLUMN IF NOT EXISTS business_line VARCHAR(120);"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE participants ADD COLUMN IF NOT EXISTS performance_history JSONB DEFAULT '{}'::jsonb;"
                )
            )
    except Exception as e:
        print(f"Auto-migration warning: {e}")

run_auto_migrations()

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
app.include_router(competency_bank.router, prefix="/competency-bank", tags=["competency-bank"])
