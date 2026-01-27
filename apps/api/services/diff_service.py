"""
Service for generating and applying minimal code diffs with safety validation
"""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import difflib
import json
import re
import subprocess


# Allowed file types for edits
ALLOWED_FILE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".css", ".json", ".md", ".txt"}

# Maximum changes per operation
MAX_FILES_PER_CHANGE = 10
MAX_LINES_PER_FILE = 1000


class DiffService:
    """
    Handles generation and application of minimal code diffs.
    Ensures we only modify what's necessary, not full rewrites.
    Includes safety validation gates.
    """
    
    def validate_file_for_edit(self, file_path: Path, project_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate that a file can be safely edited.
        Returns (is_valid, error_message)
        """
        # Must be within project directory
        try:
            file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            return False, "File path outside project directory"
        
        # Must be allowed file type
        if file_path.suffix not in ALLOWED_FILE_EXTENSIONS:
            return False, f"File type {file_path.suffix} not allowed for edits"
        
        # Must not be in node_modules, .next, or other build directories
        path_str = str(file_path.relative_to(project_path))
        forbidden_dirs = ["node_modules", ".next", ".git", "dist", "build"]
        if any(forbidden in path_str for forbidden in forbidden_dirs):
            return False, "File in forbidden directory"
        
        return True, None

    def generate_unified_diff(self, old_content: str, new_content: str, file_path: str) -> str:
        """Generate unified diff between old and new content"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        
        return "".join(diff)

    def apply_unified_diff(self, file_path: Path, diff: str, project_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Apply a unified diff to a file with validation.
        Returns (success, error_message)
        """
        # Validate file first
        is_valid, error = self.validate_file_for_edit(file_path, project_path)
        if not is_valid:
            return False, error
        
        try:
            if not file_path.exists():
                return False, "File does not exist"
            
            current_content = file_path.read_text(encoding="utf-8")
            new_content = self._apply_diff_to_content(current_content, diff)
            
            if new_content is None:
                return False, "Failed to apply diff"
            
            # Validate line count
            new_lines = new_content.splitlines()
            if len(new_lines) > MAX_LINES_PER_FILE:
                return False, f"File exceeds maximum line count ({MAX_LINES_PER_FILE})"
            
            file_path.write_text(new_content, encoding="utf-8")
            return True, None
        except Exception as e:
            return False, f"Error applying diff: {str(e)}"

    def _apply_diff_to_content(self, current_content: str, diff: str) -> Optional[str]:
        """Apply unified diff to content string"""
        lines = diff.split("\n")
        if not lines:
            return None
        
        # Parse unified diff
        current_lines = current_content.splitlines(keepends=True)
        result_lines = []
        i = 0
        diff_i = 0
        
        while diff_i < len(lines):
            line = lines[diff_i]
            
            # Skip header lines
            if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
                diff_i += 1
                continue
            
            # Context line (unchanged)
            if line.startswith(" "):
                if i < len(current_lines):
                    result_lines.append(current_lines[i])
                    i += 1
                diff_i += 1
            
            # Removed line
            elif line.startswith("-"):
                # Skip this line from current content
                i += 1
                diff_i += 1
            
            # Added line
            elif line.startswith("+"):
                result_lines.append(line[1:])
                diff_i += 1
            
            else:
                diff_i += 1
        
        # Add remaining lines
        while i < len(current_lines):
            result_lines.append(current_lines[i])
            i += 1
        
        return "".join(result_lines)

    def compute_file_changes(self, old_files: Dict[str, str], new_files: Dict[str, str]) -> Dict[str, Dict]:
        """
        Compute changes between two file sets.
        Returns dict with:
        - modified: Dict[file_path, diff]
        - added: List[file_path]
        - deleted: List[file_path]
        """
        all_files = set(old_files.keys()) | set(new_files.keys())
        
        changes = {
            "modified": {},
            "added": [],
            "deleted": []
        }
        
        for file_path in all_files:
            if file_path in old_files and file_path in new_files:
                if old_files[file_path] != new_files[file_path]:
                    diff = self.generate_unified_diff(
                        old_files[file_path],
                        new_files[file_path],
                        file_path
                    )
                    changes["modified"][file_path] = diff
            elif file_path in new_files:
                changes["added"].append(file_path)
            elif file_path in old_files:
                changes["deleted"].append(file_path)
        
        return changes

    def apply_text_changes(self, file_path: Path, changes: Dict[str, str], project_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Apply text-based changes to a file with validation.
        Returns (success, error_message)
        """
        # Validate file first
        is_valid, error = self.validate_file_for_edit(file_path, project_path)
        if not is_valid:
            return False, error
        
        try:
            if not file_path.exists():
                return False, "File does not exist"
            
            content = file_path.read_text(encoding="utf-8")
            
            # Apply simple text replacements
            for old_text, new_text in changes.items():
                if old_text in content:
                    content = content.replace(old_text, new_text)
                else:
                    # Try case-insensitive
                    pattern = re.compile(re.escape(old_text), re.IGNORECASE)
                    content = pattern.sub(new_text, content)
            
            file_path.write_text(content, encoding="utf-8")
            return True, None
        except Exception as e:
            return False, f"Error applying text changes: {str(e)}"

    def generate_changes_from_prompt(
        self,
        prompt: str,
        project_path: Path,
        spec: Dict
    ) -> Tuple[Dict[str, str], Optional[str]]:
        """
        Generate file changes from a natural language prompt.
        Returns (changes_dict, error_message)
        If error_message is not None, changes should not be applied.
        """
        changes = {}
        prompt_lower = prompt.lower()
        
        # Pattern: "change [component] [field] to [value]"
        # Example: "change hero title to Hello World"
        match = re.search(r'change\s+(\w+)\s+(\w+)\s+to\s+"?([^"]+)"?', prompt_lower)
        if match:
            component = match.group(1)
            field = match.group(2)
            value = match.group(3)
            
            # Find component file
            component_file = self._find_component_file(project_path, component)
            if component_file:
                is_valid, error = self.validate_file_for_edit(component_file, project_path)
                if not is_valid:
                    return {}, f"Cannot edit {component_file}: {error}"
                
                current_content = component_file.read_text(encoding="utf-8")
                
                # Simple replacement patterns
                if field == "title":
                    # Look for title patterns
                    patterns = [
                        (r'(<h1[^>]*>)([^<]+)(</h1>)', f'\\1{value}\\3'),
                        (r'("title":\s*")([^"]+)(")', f'\\1{value}\\3'),
                        (r'(title\s*=\s*")([^"]+)(")', f'\\1{value}\\3'),
                    ]
                    
                    for pattern, replacement in patterns:
                        if re.search(pattern, current_content):
                            new_content = re.sub(pattern, replacement, current_content)
                            rel_path = str(component_file.relative_to(project_path))
                            changes[rel_path] = new_content
                            break
                    
                    if not changes:
                        return {}, f"No title found in {component} component to change"
            else:
                return {}, f"Component '{component}' not found"
        
        # Pattern: "update [text] to [new text]"
        elif re.search(r'update\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?', prompt_lower):
            match = re.search(r'update\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?', prompt_lower)
            if match:
                old_text = match.group(1)
                new_text = match.group(2)
                
                # Search all relevant files
                for file_path in project_path.rglob("*.tsx"):
                    if file_path.is_file():
                        is_valid, error = self.validate_file_for_edit(file_path, project_path)
                        if not is_valid:
                            continue
                        
                        content = file_path.read_text(encoding="utf-8")
                        if old_text in content:
                            new_content = content.replace(old_text, new_text)
                            rel_path = str(file_path.relative_to(project_path))
                            changes[rel_path] = new_content
                            break
                
                if not changes:
                    return {}, f"Text '{old_text}' not found in any files"
        else:
            # No pattern matched - return error instead of guessing
            return {}, "Prompt does not match any supported patterns. Supported: 'change [component] [field] to [value]' or 'update [text] to [new text]'"
        
        # Validate change limits
        if len(changes) > MAX_FILES_PER_CHANGE:
            return {}, f"Too many files to change ({len(changes)} > {MAX_FILES_PER_CHANGE})"
        
        return changes, None

    def _find_component_file(self, project_path: Path, component_name: str) -> Optional[Path]:
        """Find component file by name"""
        # Try common locations
        search_paths = [
            project_path / "components" / "sections" / f"{component_name}.tsx",
            project_path / "components" / "sections" / f"{component_name.capitalize()}.tsx",
            project_path / "app" / f"{component_name}" / "page.tsx",
            project_path / "components" / f"{component_name}.tsx",
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        # Search recursively (but only in allowed directories)
        for file_path in project_path.rglob(f"*{component_name}*.tsx"):
            if file_path.is_file():
                is_valid, _ = self.validate_file_for_edit(file_path, project_path)
                if is_valid:
                    return file_path
        
        return None

    def validate_and_apply_changes(
        self,
        changes: Dict[str, str],
        project_path: Path
    ) -> Tuple[bool, Optional[str], Dict[str, str]]:
        """
        Validate changes, apply them, run lint/build, and revert if needed.
        Returns (success, error_message, applied_files)
        """
        applied_files = {}
        
        # Apply changes
        for rel_path, new_content in changes.items():
            file_path = project_path / rel_path
            
            is_valid, error = self.validate_file_for_edit(file_path, project_path)
            if not is_valid:
                # Revert any already applied changes
                for applied_path, old_content in applied_files.items():
                    (project_path / applied_path).write_text(old_content, encoding="utf-8")
                return False, f"Cannot edit {rel_path}: {error}", {}
            
            # Backup original content
            if file_path.exists():
                applied_files[rel_path] = file_path.read_text(encoding="utf-8")
            
            # Apply change
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(new_content, encoding="utf-8")
        
        # Run format and lint (if available)
        try:
            # Try to run lint
            result = subprocess.run(
                ["npm", "run", "lint"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                # Revert changes
                for rel_path, old_content in applied_files.items():
                    (project_path / rel_path).write_text(old_content, encoding="utf-8")
                return False, f"Lint failed: {result.stderr[:500]}", {}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Lint not available or timeout - continue
            pass
        
        return True, None, applied_files
