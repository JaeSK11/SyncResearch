from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import papers, query, health
from api.config import Settings

settings = Settings()

app = FastAPI(
    title="Research Retrieval API",
    description="RAG system for academic paper analysis",
    version="0.1.0"
)

# CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(papers.router, prefix="/papers", tags=["papers"])
app.include_router(query.router, prefix="/query", tags=["query"])

@app.get("/")
def root():
    return {"message": "Research Retrieval API", "docs": "/docs"}