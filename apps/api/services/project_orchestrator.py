"""
Project orchestrator service - handles project creation, iteration, and builds
"""
import os
import json
import shutil
import uuid
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models import (
    Project, ProjectVersion, Build, ChatMessage, ProjectStatus, BuildStatus
)
from services.build_service import BuildService
from services.repair_service import RepairService
from services.diff_service import DiffService
from services.credit_service import charge_credits, InsufficientCreditsError
from config.credits import CREDIT_COSTS
from schemas import ErrorResponse, ErrorDetail

PROJECTS_DIR = Path(os.getenv("PROJECTS_DIR", "./projects"))
TEMPLATES_DIR = Path(os.getenv("TEMPLATES_DIR", "./templates"))
STABLE_TEMPLATE = "nextjs-stable"

# Change size classification rules (deterministic)
# Small: Single file, < 50 lines changed, simple text replacement
# Medium: 1-3 files, 50-200 lines changed, component updates
# Large: > 3 files, > 200 lines changed, structural changes
CHANGE_SIZE_RULES = {
    "small": {
        "max_files": 1,
        "max_lines": 50,
        "patterns": ["change", "update", "replace", "fix typo"]
    },
    "medium": {
        "max_files": 3,
        "max_lines": 200,
        "patterns": ["add", "remove", "modify", "update component"]
    },
    "large": {
        "max_files": float("inf"),
        "max_lines": float("inf"),
        "patterns": ["refactor", "restructure", "redesign", "major"]
    }
}


class ProjectOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.build_service = BuildService(PROJECTS_DIR)
        self.repair_service = RepairService()
        self.diff_service = DiffService()
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    def create_project(
        self,
        user_id: str,
        name: str,
        prompt: str
    ) -> Tuple[Project, ProjectVersion, Build]:
        """
        Create a new project from prompt.
        Charges credits and creates initial version and build.
        """
        # Charge credits
        try:
            new_balance, transaction_id = charge_credits(
                self.db,
                user_id,
                CREDIT_COSTS["create_project"],
                f"Create project: {name}",
                None
            )
        except InsufficientCreditsError as e:
            raise ValueError(str(e))

        # Create project
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            user_id=user_id,
            name=name,
            initial_prompt=prompt,
            description=prompt[:200] if len(prompt) > 200 else prompt,
            current_spec=self._generate_initial_spec(prompt),
            status=ProjectStatus.BUILDING,
            watermark_enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(project)

        # Create initial version
        version = self._create_version(project_id, project.current_spec, "system")
        self.db.add(version)

        # Generate and build
        build = self._build_project(project, version)

        # Update project status
        if build.status == BuildStatus.SUCCESS:
            project.status = ProjectStatus.READY
            project.preview_url = build.preview_url
        else:
            project.status = ProjectStatus.FAILED

        self.db.commit()
        self.db.refresh(project)
        self.db.refresh(version)
        self.db.refresh(build)

        return project, version, build

    def iterate_project(
        self,
        project_id: str,
        user_id: str,
        message: str
    ) -> Tuple[ProjectVersion, Build, str, float, Dict]:
        """
        Process a chat iteration on a project.
        Returns (version, build, change_size, credits_charged, credit_info)
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        if project.user_id != user_id:
            raise ValueError("Unauthorized")

        # Store chat message
        chat_msg = ChatMessage(
            id=str(uuid.uuid4()),
            project_id=project_id,
            user_id=user_id,
            role="user",
            content=message,
            created_at=datetime.utcnow()
        )
        self.db.add(chat_msg)

        # Get current project files for diff calculation
        project_path = self.build_service.get_project_path(project_id)
        old_files = self._get_all_project_files(project_path) if project_path.exists() else {}

        # Update spec (placeholder - will use AI later)
        updated_spec = self._update_spec_from_message(project.current_spec, message)
        project.current_spec = updated_spec
        project.status = ProjectStatus.BUILDING

        # Generate real file changes from prompt
        file_changes, error_message = self.diff_service.generate_changes_from_prompt(
            message,
            project_path,
            updated_spec
        )

        # If no changes or error, return error
        if error_message:
            self.db.rollback()
            raise ValueError(f"Cannot process prompt: {error_message}")

        # Validate and apply changes with safety checks
        if file_changes:
            success, error, applied_files = self.diff_service.validate_and_apply_changes(
                file_changes,
                project_path
            )
            
            if not success:
                # Revert any changes
                for rel_path, old_content in applied_files.items():
                    (project_path / rel_path).write_text(old_content, encoding="utf-8")
                self.db.rollback()
                raise ValueError(f"Failed to apply changes: {error}")

        # Get new files for diff
        new_files = self._get_all_project_files(project_path)
        
        # Compute unified diff
        file_changes_dict = self.diff_service.compute_file_changes(old_files, new_files)
        
        # Determine change size (deterministic rules)
        change_size, rule_applied = self._determine_change_size_deterministic(
            message, file_changes_dict, project
        )
        credit_cost = CREDIT_COSTS.get(f"{change_size}_edit", CREDIT_COSTS["medium_edit"])
        
        # Log change size determination for transparency
        logger = logging.getLogger(__name__)
        logger.info(f"Change size: {change_size}, Credit cost: {credit_cost}, Rule: {rule_applied}")

        # Charge credits
        try:
            new_balance, transaction_id = charge_credits(
                self.db,
                user_id,
                credit_cost,
                f"{change_size.title()} edit on {project.name}",
                project_id
            )
            credit_info = {
                "charged_action": f"{change_size}_edit",
                "charged_amount": credit_cost,
                "wallet_balance_after": new_balance,
                "transaction_id": transaction_id,
                "rule_applied": rule_applied
            }
        except InsufficientCreditsError as e:
            self.db.rollback()
            raise ValueError(str(e))

        # Create diff patch (JSON format for storage)
        diff_patch = {
            "modified": file_changes_dict.get("modified", {}),
            "added": file_changes_dict.get("added", []),
            "deleted": file_changes_dict.get("deleted", [])
        }

        # Create new version
        version = self._create_version(project_id, updated_spec, user_id, diff_patch)
        self.db.add(version)

        # Build project with repair loop
        build = self._build_project_with_repair(project, version, project_path)

        # Update project status
        if build.status == BuildStatus.SUCCESS:
            project.status = ProjectStatus.READY
            project.preview_url = build.preview_url
        else:
            project.status = ProjectStatus.FAILED

        self.db.commit()
        self.db.refresh(version)
        self.db.refresh(build)

        return version, build, change_size, credit_cost, credit_info

    def _determine_change_size_deterministic(
        self,
        message: str,
        file_changes: Dict,
        project: Project
    ) -> Tuple[str, str]:
        """
        Determine change size using deterministic rules.
        Returns (change_size, rule_applied)
        """
        message_lower = message.lower()
        num_files_changed = (
            len(file_changes.get("modified", {})) +
            len(file_changes.get("added", [])) +
            len(file_changes.get("deleted", []))
        )
        
        # Count total lines changed
        total_lines = 0
        for diff in file_changes.get("modified", {}).values():
            total_lines += diff.count("\n+") + diff.count("\n-")

        # Apply rules in order: small -> medium -> large
        for size, rules in CHANGE_SIZE_RULES.items():
            max_files = rules["max_files"]
            max_lines = rules["max_lines"]
            patterns = rules["patterns"]
            
            # Check if message matches patterns
            matches_pattern = any(pattern in message_lower for pattern in patterns)
            
            # Check file and line limits
            within_limits = (
                num_files_changed <= max_files and
                total_lines <= max_lines
            )
            
            if matches_pattern or within_limits:
                rule_applied = f"{size}: files={num_files_changed}<={max_files}, lines={total_lines}<={max_lines}, pattern_match={matches_pattern}"
                return size, rule_applied
        
        # Default to medium
        return "medium", "default: no rule matched"

    def _get_all_project_files(self, project_path: Path) -> Dict[str, str]:
        """Get all project files as dict of rel_path -> content"""
        files = {}
        if not project_path.exists():
            return files
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    rel_path = str(file_path.relative_to(project_path))
                    # Skip node_modules and build outputs
                    if "node_modules" not in rel_path and ".next" not in rel_path:
                        content = file_path.read_text(encoding="utf-8")
                        files[rel_path] = content
                except Exception:
                    pass  # Skip binary files
        
        return files

    def _generate_initial_spec(self, prompt: str) -> Dict:
        """Generate initial project specification from prompt (placeholder)"""
        # TODO: Use AI to parse prompt into structured spec
        return {
            "prompt": prompt,
            "pages": ["home", "pricing", "about", "contact"],
            "components": ["Header", "Footer", "Hero", "Features", "CTA"],
            "theme": {
                "primary_color": "#3b82f6",
                "secondary_color": "#64748b",
                "accent_color": "#f59e0b"
            }
        }

    def _update_spec_from_message(self, current_spec: Dict, message: str) -> Dict:
        """Update spec based on chat message (placeholder)"""
        # TODO: Use AI to update spec based on message
        updated = current_spec.copy()
        updated["last_update"] = message
        updated["updated_at"] = datetime.utcnow().isoformat()
        return updated

    def _create_version(
        self,
        project_id: str,
        spec_snapshot: Dict,
        created_by: str,
        code_diff: Optional[Dict] = None
    ) -> ProjectVersion:
        """Create a new project version"""
        # Get next version number
        last_version = self.db.query(ProjectVersion).filter(
            ProjectVersion.project_id == project_id
        ).order_by(ProjectVersion.version_number.desc()).first()
        
        version_number = (last_version.version_number + 1) if last_version else 1

        version = ProjectVersion(
            id=str(uuid.uuid4()),
            project_id=project_id,
            version_number=version_number,
            spec_snapshot=spec_snapshot,
            code_diff=code_diff,
            created_at=datetime.utcnow(),
            created_by=created_by
        )
        return version

    def _build_project_with_repair(
        self,
        project: Project,
        version: ProjectVersion,
        project_path: Path
    ) -> Build:
        """Build a project version with repair loop"""
        attempt = 1
        max_attempts = 3
        build_id = str(uuid.uuid4())

        while attempt <= max_attempts:
            build_status = BuildStatus.BUILDING if attempt == 1 else BuildStatus.REPAIRING
            
            build = Build(
                id=build_id,
                project_id=project.id,
                version_id=version.id,
                status=build_status,
                attempt_number=attempt,
                created_at=datetime.utcnow()
            )
            self.db.add(build)
            self.db.commit()

            # Run build
            success, results = self.build_service.validate_build(project.id, project_path)

            # Sanitize logs to redact secrets
            from services.log_sanitizer import sanitize_logs
            build.build_logs = sanitize_logs(results.get("logs", ""))
            build.lint_output = sanitize_logs(results.get("lint_output", ""))
            build.build_output = sanitize_logs(results.get("build_output", ""))
            build.error_message = sanitize_logs(results.get("error", ""))

            if success:
                build.status = BuildStatus.SUCCESS
                build.completed_at = datetime.utcnow()
                build.preview_url = f"http://localhost:3000/preview/{project.id}/{build.id}"
                self.db.commit()
                return build
            else:
                build.status = BuildStatus.FAILED
                build.completed_at = datetime.utcnow()
                self.db.commit()

                # Try repair
                if attempt < max_attempts:
                    error_analysis = self.repair_service.analyze_failure(
                        build.build_logs or "",
                        build.lint_output or "",
                        build.build_output or ""
                    )
                    
                    repair_patch = self.repair_service.generate_repair_patch(
                        error_analysis,
                        project.current_spec,
                        project_path,
                        build.build_logs or ""
                    )
                    
                    if repair_patch:
                        # Apply repair patch with validation
                        repair_success = True
                        for rel_path, new_content in repair_patch.items():
                            file_path = project_path / rel_path
                            is_valid, error = self.diff_service.validate_file_for_edit(file_path, project_path)
                            if not is_valid:
                                repair_success = False
                                print(f"[REPAIR] Cannot repair {rel_path}: {error}")
                                break
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            file_path.write_text(new_content, encoding="utf-8")
                        
                        if repair_success:
                            # Log repair attempt
                            build.build_logs = f"{build.build_logs}\n\n[REPAIR ATTEMPT {attempt + 1}]\nApplied fixes: {list(repair_patch.keys())}\nFiles changed: {len(repair_patch)}\n"
                            self.db.commit()
                            
                            # Use repair_build for repair attempts
                            success, results = self.build_service.repair_build(
                                project.id,
                                project_path,
                                build.build_logs or ""
                            )
                            
                            # Update build with repair results
                            from services.log_sanitizer import sanitize_logs
                            build.build_logs = sanitize_logs(results.get("logs", ""))
                            build.lint_output = sanitize_logs(results.get("lint_output", ""))
                            build.build_output = sanitize_logs(results.get("build_output", ""))
                            build.error_message = sanitize_logs(results.get("error", ""))
                            
                            if success:
                                build.status = BuildStatus.SUCCESS
                                build.completed_at = datetime.utcnow()
                                build.preview_url = f"http://localhost:3000/preview/{project.id}/{build.id}"
                                self.db.commit()
                                return build
                            else:
                                build.status = BuildStatus.FAILED
                                build.completed_at = datetime.utcnow()
                                self.db.commit()
                                attempt += 1
                                continue
                        else:
                            # Repair patch invalid, stop retrying
                            build.build_logs = f"{build.build_logs}\n\n[REPAIR ATTEMPT {attempt + 1} FAILED]\nRepair patch validation failed\n"
                            self.db.commit()
                            break

                # No repair possible or max attempts reached
                return build

        return build

    def _build_project(self, project: Project, version: ProjectVersion) -> Build:
        """Build a project version (legacy method, calls _build_project_with_repair)"""
        project_path = self.build_service.get_project_path(project.id)
        if not project_path.exists():
            self._initialize_project_directory(project, project_path)
        return self._build_project_with_repair(project, version, project_path)

    def _initialize_project_directory(self, project: Project, project_path: Path):
        """Initialize project directory from stable template"""
        template_path = TEMPLATES_DIR / STABLE_TEMPLATE
        if not template_path.exists():
            raise ValueError(f"Template {STABLE_TEMPLATE} not found")

        # Copy template
        shutil.copytree(template_path, project_path)

        # Replace placeholders
        self._replace_placeholders(project_path, project)

    def _replace_placeholders(self, directory: Path, project: Project):
        """Replace template placeholders with project values"""
        spec = project.current_spec
        replacements = {
            "{{PROJECT_NAME}}": project.name,
            "{{PROJECT_NAME_LOWER}}": project.name.lower().replace(" ", "-"),
            "{{PROJECT_DESCRIPTION}}": project.description or "",
            "{{YEAR}}": str(datetime.utcnow().year),
            "{{PRIMARY_COLOR}}": spec.get("theme", {}).get("primary_color", "#3b82f6"),
            "{{SECONDARY_COLOR}}": spec.get("theme", {}).get("secondary_color", "#64748b"),
            "{{ACCENT_COLOR}}": spec.get("theme", {}).get("accent_color", "#f59e0b"),
            "{{PROJECT_DOMAIN}}": f"{project.name.lower().replace(' ', '-')}.com"
        }

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt", ".css"]:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    for old, new in replacements.items():
                        content = content.replace(old, new)
                    file_path.write_text(content, encoding="utf-8")
                except Exception:
                    pass  # Skip binary files
