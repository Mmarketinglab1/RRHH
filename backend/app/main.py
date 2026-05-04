from fastapi import FastAPI

from app.api.middleware import TenantContextMiddleware
from app.api.routes import ai, auth, competencies, evaluations, participants, results, surveys

app = FastAPI(title="Evaluation 360 AI SaaS", version="0.1.0")
app.add_middleware(TenantContextMiddleware)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
app.include_router(competencies.router, prefix="/evaluations", tags=["competencies"])
app.include_router(participants.router, prefix="/evaluations", tags=["participants"])
app.include_router(surveys.router, prefix="/surveys", tags=["surveys"])
app.include_router(results.router, prefix="/evaluations", tags=["results"])
app.include_router(ai.router, prefix="/evaluations", tags=["ai"])
