"""
Auto-repair service for fixing build failures with constraints
"""
from typing import Dict, List, Optional
from pathlib import Path
import json
import re


class RepairService:
    """
    Analyzes build failures and attempts to generate minimal fixes.
    Includes constraints to prevent excessive changes.
    """
    
    def __init__(self):
        self.max_repair_attempts = 3
        self.max_files_per_repair = 3  # Limit files changed per repair
        self.max_lines_per_repair = 50  # Limit lines changed per repair
        self.files_changed_count = 0
        self.lines_changed_count = 0

    def analyze_failure(self, build_logs: str, lint_output: str, build_output: str) -> Dict:
        """
        Analyze build failure and return repair suggestions.
        Returns dict with:
        - error_type: str (e.g., "syntax_error", "missing_dependency", "type_error")
        - suggestions: List[str] of suggested fixes
        - confidence: float 0-1
        - fixable: bool - whether we can auto-fix this
        """
        error_type = "unknown"
        suggestions = []
        confidence = 0.0
        fixable = False
        all_logs = f"{build_logs}\n{lint_output}\n{build_output}"

        # Pattern matching for common errors
        if "Cannot find module" in all_logs or "Module not found" in all_logs:
            error_type = "missing_dependency"
            # Extract module name
            match = re.search(r"Cannot find module ['\"]([^'\"]+)['\"]", all_logs)
            if match:
                module_name = match.group(1)
                suggestions.append(f"Add missing dependency: {module_name}")
                confidence = 0.8
                fixable = True
            else:
                suggestions.append("Add missing dependency to package.json")
                confidence = 0.7
        elif "SyntaxError" in all_logs or "Unexpected token" in all_logs:
            error_type = "syntax_error"
            # Extract file and line
            match = re.search(r"SyntaxError.*?\((\d+):(\d+)\)", all_logs)
            if match:
                line_num = match.group(1)
                suggestions.append(f"Fix syntax error around line {line_num}")
                confidence = 0.8
            else:
                suggestions.append("Fix syntax error in source code")
                confidence = 0.7
        elif "Type error" in all_logs or "TypeError" in all_logs or "TS" in all_logs:
            error_type = "type_error"
            # Extract TypeScript error details
            match = re.search(r"TS\d+.*?\((\d+):(\d+)\)", all_logs)
            if match:
                line_num = match.group(1)
                suggestions.append(f"Fix TypeScript error at line {line_num}")
                confidence = 0.6
            else:
                suggestions.append("Fix TypeScript type errors")
                confidence = 0.5
        elif "ESLint" in all_logs or "eslint" in all_logs:
            error_type = "lint_error"
            # Extract ESLint errors
            matches = re.findall(r"(\d+):(\d+)\s+error\s+(.+?)\s+", all_logs)
            if matches:
                for line, col, msg in matches[:3]:  # Limit to first 3
                    suggestions.append(f"Line {line}: {msg}")
                confidence = 0.9
                fixable = True
            else:
                suggestions.append("Fix ESLint errors")
                confidence = 0.8
        elif "import" in all_logs.lower() and "error" in all_logs.lower():
            error_type = "import_error"
            suggestions.append("Fix import statements")
            confidence = 0.6

        return {
            "error_type": error_type,
            "suggestions": suggestions,
            "confidence": confidence,
            "fixable": fixable
        }

    def generate_repair_patch(
        self,
        error_analysis: Dict,
        project_spec: Dict,
        project_path: Path,
        build_logs: str
    ) -> Optional[Dict[str, str]]:
        """
        Generate a minimal code patch to fix the issue with constraints.
        Returns dict of file_path -> new_content, or None if repair not possible.
        """
        if not error_analysis.get("fixable", False):
            return None

        # Reset counters for this repair attempt
        self.files_changed_count = 0
        self.lines_changed_count = 0

        error_type = error_analysis.get("error_type")
        patches = {}

        if error_type == "missing_dependency":
            # Only add dependency if explicitly needed and logged
            package_json = project_path / "package.json"
            if package_json.exists() and self.files_changed_count < self.max_files_per_repair:
                try:
                    package_data = json.loads(package_json.read_text())
                    # Extract module name from logs
                    match = re.search(r"Cannot find module ['\"]([^'\"]+)['\"]", build_logs)
                    if match:
                        module_name = match.group(1)
                        # Clean module name (remove @scope if present, get base name)
                        base_name = module_name.split("/")[-1].split("@")[0]
                        
                        if "dependencies" not in package_data:
                            package_data["dependencies"] = {}
                        
                        # Only add if not already present
                        if base_name not in package_data["dependencies"]:
                            package_data["dependencies"][base_name] = "^latest"
                            patches["package.json"] = json.dumps(package_data, indent=2)
                            self.files_changed_count += 1
                            # Log the addition
                            print(f"[REPAIR] Adding dependency: {base_name}")
                except Exception as e:
                    print(f"Error repairing package.json: {e}")

        elif error_type == "syntax_error":
            # Try to fix common syntax errors (minimal changes)
            match = re.search(r"SyntaxError.*?\((\d+):(\d+)\)", build_logs)
            if match and self.files_changed_count < self.max_files_per_repair:
                # Find the file with the error (from stack trace)
                file_match = re.search(r"at\s+([^\s]+\.(tsx?|jsx?))", build_logs)
                if file_match:
                    file_name = file_match.group(1)
                    file_path = project_path / file_name
                    if file_path.exists():
                        content = file_path.read_text(encoding="utf-8")
                        lines = content.splitlines()
                        line_num = int(match.group(1)) - 1
                        
                        if 0 <= line_num < len(lines):
                            # Common fixes (minimal)
                            line = lines[line_num]
                            original_line = line
                            
                            # Fix missing semicolon (only if line count allows)
                            if not line.rstrip().endswith((";", "{", "}", ")", "]", ",")):
                                lines[line_num] = line.rstrip() + ";"
                                self.lines_changed_count += 1
                            # Fix unclosed quotes (only if line count allows)
                            elif line.count('"') % 2 != 0 and self.lines_changed_count < self.max_lines_per_repair:
                                lines[line_num] = line.rstrip() + '"'
                                self.lines_changed_count += 1
                            
                            if lines[line_num] != original_line:
                                patches[str(file_path.relative_to(project_path))] = "\n".join(lines) + "\n"
                                self.files_changed_count += 1
                                print(f"[REPAIR] Fixed syntax error in {file_name}")

        elif error_type == "lint_error":
            # Fix common ESLint errors (limited to max_files_per_repair)
            matches = re.findall(r"(\d+):(\d+)\s+error\s+(.+?)\s+", build_logs)
            file_match = re.search(r"(.+\.(tsx?|jsx?))", build_logs)
            if file_match and matches and self.files_changed_count < self.max_files_per_repair:
                file_name = file_match.group(1)
                file_path = project_path / file_name
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8")
                    lines = content.splitlines()
                    
                    # Limit fixes to prevent excessive changes
                    fixes_applied = 0
                    for line_str, col_str, msg in matches[:3]:  # Fix first 3 errors max
                        if fixes_applied >= 3 or self.lines_changed_count >= self.max_lines_per_repair:
                            break
                        
                        line_num = int(line_str) - 1
                        if 0 <= line_num < len(lines):
                            line = lines[line_num]
                            
                            # Fix unused variable (minimal change)
                            if "is assigned a value but never used" in msg:
                                # Comment out the line
                                lines[line_num] = f"// {line}"
                                self.lines_changed_count += 1
                                fixes_applied += 1
                            
                            # Fix missing return type (minimal change)
                            elif "missing return type" in msg.lower() and ":" not in line:
                                # Add : any return type (simple fix)
                                lines[line_num] = line.replace("function", "function: any")
                                self.lines_changed_count += 1
                                fixes_applied += 1
                    
                    if fixes_applied > 0:
                        patches[str(file_path.relative_to(project_path))] = "\n".join(lines) + "\n"
                        self.files_changed_count += 1
                        print(f"[REPAIR] Fixed {fixes_applied} ESLint errors in {file_name}")

        # Enforce limits
        if self.files_changed_count > self.max_files_per_repair:
            print(f"[REPAIR] Exceeded max files limit ({self.max_files_per_repair})")
            return None
        
        if self.lines_changed_count > self.max_lines_per_repair:
            print(f"[REPAIR] Exceeded max lines limit ({self.max_lines_per_repair})")
            return None

        return patches if patches else None

    def should_retry(self, attempt_number: int) -> bool:
        """Check if we should retry based on attempt number"""
        return attempt_number < self.max_repair_attempts

    def reset_counters(self):
        """Reset change counters for new repair cycle"""
        self.files_changed_count = 0
        self.lines_changed_count = 0
