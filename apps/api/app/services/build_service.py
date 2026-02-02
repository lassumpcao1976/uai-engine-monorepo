import httpx
from sqlalchemy.orm import Session
from app.models.build import Build, BuildStatus
from app.models.version import Version
from app.core.config import settings
from app.core.logging import logger


class BuildService:
    @staticmethod
    async def create_build(version: Version, db: Session) -> Build:
        build = Build(
            project_id=version.project_id,
            version_id=version.id,
            status=BuildStatus.PENDING,
        )
        db.add(build)
        db.commit()
        db.refresh(build)
        
        # Trigger build in runner service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.runner_url}/builds",
                    json={
                        "build_id": build.id,
                        "version_id": version.id,
                        "project_id": version.project_id,
                        "prompt": version.prompt,
                    },
                    timeout=30.0,
                )
                if response.status_code == 200:
                    build.status = BuildStatus.RUNNING
                    db.commit()
                    logger.info("build_started", build_id=build.id)
                else:
                    build.status = BuildStatus.FAILED
                    build.error_message = f"Runner service error: {response.status_code}"
                    db.commit()
        except Exception as e:
            build.status = BuildStatus.FAILED
            build.error_message = str(e)
            db.commit()
            logger.error("build_start_failed", build_id=build.id, error=str(e))
        
        return build

    @staticmethod
    def update_build_status(
        build_id: int,
        status: BuildStatus,
        logs: str | None = None,
        preview_url: str | None = None,
        error_message: str | None = None,
        db: Session = None,
    ):
        build = db.query(Build).filter(Build.id == build_id).first()
        if not build:
            return None
        
        build.status = status
        if logs is not None:
            build.logs = logs
        if preview_url is not None:
            build.preview_url = preview_url
        if error_message is not None:
            build.error_message = error_message
        
        if status in [BuildStatus.SUCCESS, BuildStatus.FAILED, BuildStatus.CANCELLED]:
            from datetime import datetime
            build.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(build)
        logger.info("build_status_updated", build_id=build_id, status=status.value)
        return build
