from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.policies import router as policies_router
from app.api.auth import router as auth_router
from app.api.policy_versions import (
    router as policy_versions_router
)

app = FastAPI(
    title="Policy Change Impact Analysis API",
    version="1.0.0"
)
from app.api.regulatory_changes import (
    router as regulatory_changes_router
)

from app.api.policy_relationships import (
    router as policy_relationships_router
)
from app.api.legal_rag import router as legal_rag_router
from app.api.change_engine import router as change_engine_router
from app.api.impact_engine import router as impact_engine_router
from app.api.impact_analysis import router as impact_analysis_router
from app.api.documents import router as documents_router
app.include_router(
    change_engine_router,
    prefix="/api",
)
from app.api.explainable_rag import (
    router as explainable_rag_router,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(policies_router)
app.include_router(policy_versions_router)
app.include_router(regulatory_changes_router)
app.include_router(policy_relationships_router)
app.include_router(
    legal_rag_router,
    prefix="/api",
)
app.include_router(
    impact_analysis_router,
    prefix="/api",
)
app.include_router(
    impact_engine_router,
    prefix="/api",
)
app.include_router(
    documents_router,
    prefix="/api",
)
app.include_router(change_engine_router)
app.include_router(
    explainable_rag_router,
    prefix="/api",
)
@app.get("/")
def root():
    return {
        "message": "Policy Change Impact Analysis API is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "connected",
        "frontend": "ready",
        "backend": "ready"
    }