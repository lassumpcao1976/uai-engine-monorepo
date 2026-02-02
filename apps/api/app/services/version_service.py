import difflib
from sqlalchemy.orm import Session
from app.models.version import Version
from app.models.project import Project
from typing import Any


class VersionService:
    @staticmethod
    def create_version(project: Project, prompt: str, file_tree: dict[str, Any] | None, db: Session) -> Version:
        version = Version(
            project_id=project.id,
            prompt=prompt,
            file_tree=file_tree,
        )
        
        # Generate unified diff from previous version
        previous_version = (
            db.query(Version)
            .filter(Version.project_id == project.id)
            .order_by(Version.id.desc())
            .offset(1)
            .first()
        )
        
        if previous_version and previous_version.file_tree and file_tree:
            diff = VersionService._generate_unified_diff(
                previous_version.file_tree,
                file_tree,
            )
            version.unified_diff = diff
        
        db.add(version)
        db.commit()
        db.refresh(version)
        return version

    @staticmethod
    def _generate_unified_diff(old_tree: dict[str, Any], new_tree: dict[str, Any]) -> str:
        """Generate a unified diff representation of file tree changes."""
        def tree_to_lines(tree: dict[str, Any], prefix: str = "") -> list[str]:
            lines = []
            for key, value in sorted(tree.items()):
                path = f"{prefix}/{key}" if prefix else key
                if isinstance(value, dict):
                    lines.append(f"{path}/")
                    lines.extend(tree_to_lines(value, path))
                else:
                    lines.append(f"{path}")
            return lines
        
        old_lines = tree_to_lines(old_tree)
        new_lines = tree_to_lines(new_tree)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm="",
            fromfile="previous",
            tofile="current",
        )
        return "\n".join(diff)
