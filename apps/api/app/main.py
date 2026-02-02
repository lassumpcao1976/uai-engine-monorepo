from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(
    title="UAI Engine API",
    description="UAI Engine - You think, we build.",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    logger.info("api_started", version="1.0.0")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
