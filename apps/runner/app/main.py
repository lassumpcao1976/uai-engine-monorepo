from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from app.services.build_executor import BuildExecutor
from app.core.logging import logger

app = FastAPI(title="UAI Runner Service")


class BuildRequest(BaseModel):
    build_id: int
    version_id: int
    project_id: int
    prompt: str


@app.post("/builds")
async def create_build(request: BuildRequest, background_tasks: BackgroundTasks):
    """Start a build in the background."""
    executor = BuildExecutor()
    
    # Run build in background
    background_tasks.add_task(
        executor.execute_build,
        request.build_id,
        request.version_id,
        request.project_id,
        request.prompt,
    )
    
    logger.info("build_requested", build_id=request.build_id)
    return {"status": "accepted", "build_id": request.build_id}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    logger.info("runner_started", version="1.0.0")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
