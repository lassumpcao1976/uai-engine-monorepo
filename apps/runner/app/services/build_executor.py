import os
import json
import tempfile
import subprocess
import httpx
from pathlib import Path
from typing import Dict, Any
from app.core.config import settings
from app.core.logging import logger


class BuildExecutor:
    def __init__(self):
        self.api_url = settings.api_url
        self.build_host = settings.build_host

    async def execute_build(
        self,
        build_id: int,
        version_id: int,
        project_id: int,
        prompt: str,
    ) -> Dict[str, Any]:
        """Execute a build using BuildKit."""
        logs = []
        
        try:
            logger.info("build_submitted_to_buildkit", build_id=build_id, version_id=version_id)
            await self._update_build_status(build_id, "running", logs="Build started...\n")
            
            # Create temporary directory for build
            with tempfile.TemporaryDirectory() as build_dir:
                project_path = Path(build_dir) / f"project-{project_id}"
                project_path.mkdir()
                
                logs.append("Generating project structure...\n")
                await self._generate_nextjs_project(project_path, prompt)
                
                # Generate Dockerfile
                dockerfile_content = self._generate_dockerfile()
                (project_path / "Dockerfile").write_text(dockerfile_content)
                
                # Build using BuildKit via docker buildx
                logs.append("Building with BuildKit...\n")
                image_tag = f"uai-build-{build_id}"
                
                logger.info("build_in_progress", build_id=build_id)
                
                # Create buildx builder pointing to BuildKit daemon
                builder_name = f"buildkit-{build_id}"
                create_builder_cmd = [
                    "docker", "buildx", "create",
                    "--name", builder_name,
                    "--driver", "remote",
                    "--driver-opt", f"server={self.build_host}",
                    "--use",
                ]
                
                # Create builder (ignore if already exists)
                subprocess.run(create_builder_cmd, capture_output=True, timeout=10)
                
                # Use docker buildx to connect to BuildKit daemon
                build_cmd = [
                    "docker", "buildx", "build",
                    "--builder", builder_name,
                    "--load",
                    "--tag", image_tag,
                    "--progress", "plain",
                    str(project_path),
                ]
                
                env = os.environ.copy()
                
                try:
                    process = subprocess.Popen(
                        build_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        env=env,
                        cwd=str(project_path),
                    )
                    
                    # Stream build logs
                    for line in process.stdout:
                        if line.strip():
                            logs.append(line)
                            # Update logs periodically
                            if len(logs) % 10 == 0:
                                await self._update_build_status(
                                    build_id, "running", logs="".join(logs)
                                )
                    
                    process.wait()
                    
                    if process.returncode != 0:
                        error_msg = f"BuildKit build failed with exit code {process.returncode}"
                        logs.append(error_msg + "\n")
                        logger.error("build_finished_with_status", build_id=build_id, status="failed")
                        await self._update_build_status(
                            build_id, "failed", logs="".join(logs), error_message=error_msg
                        )
                        return {"status": "failed", "logs": "".join(logs), "error": error_msg}
                    
                except Exception as e:
                    error_msg = f"BuildKit build execution failed: {str(e)}"
                    logs.append(error_msg + "\n")
                    logger.error("build_execution_failed", build_id=build_id, error=str(e))
                    await self._update_build_status(
                        build_id, "failed", logs="".join(logs), error_message=error_msg
                    )
                    return {"status": "failed", "logs": "".join(logs), "error": error_msg}
                
                # Run container using docker run (still need docker CLI for this)
                logs.append("Starting preview container...\n")
                import random
                port = random.randint(30000, 30100)
                
                run_cmd = [
                    "docker", "run",
                    "-d",
                    "--rm",
                    "-p", f"{port}:3000",
                    "--network", "bridge",
                    image_tag,
                ]
                
                try:
                    run_process = subprocess.run(
                        run_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    
                    if run_process.returncode != 0:
                        error_msg = f"Failed to start container: {run_process.stderr}"
                        logs.append(error_msg + "\n")
                        await self._update_build_status(
                            build_id, "failed", logs="".join(logs), error_message=error_msg
                        )
                        return {"status": "failed", "logs": "".join(logs), "error": error_msg}
                    
                    preview_url = f"http://localhost:{port}"
                    logs.append(f"Preview available at {preview_url}\n")
                    
                    logger.info("build_finished_with_status", build_id=build_id, status="success")
                    await self._update_build_status(
                        build_id,
                        "success",
                        logs="".join(logs),
                        preview_url=preview_url,
                    )
                    
                    return {
                        "status": "success",
                        "logs": "".join(logs),
                        "preview_url": preview_url,
                    }
                    
                except subprocess.TimeoutExpired:
                    error_msg = "Timeout starting container"
                    logs.append(error_msg + "\n")
                    await self._update_build_status(
                        build_id, "failed", logs="".join(logs), error_message=error_msg
                    )
                    return {"status": "failed", "logs": "".join(logs), "error": error_msg}
                
        except Exception as e:
            error_msg = f"Build execution failed: {str(e)}"
            logger.error("build_execution_failed", build_id=build_id, error=str(e))
            logs.append(error_msg + "\n")
            await self._update_build_status(
                build_id, "failed", logs="".join(logs), error_message=error_msg
            )
            return {"status": "failed", "logs": "".join(logs), "error": error_msg}

    async def _generate_nextjs_project(self, project_path: Path, prompt: str):
        """Generate a Next.js project structure based on prompt."""
        (project_path / "app").mkdir()
        (project_path / "public").mkdir()
        (project_path / "components").mkdir()
        
        package_json = {
            "name": "uai-project",
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
            },
            "dependencies": {
                "next": "^14.1.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
            },
        }
        (project_path / "package.json").write_text(json.dumps(package_json, indent=2))
        
        (project_path / "app" / "layout.tsx").write_text(
            """export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
"""
        )
        
        (project_path / "app" / "page.tsx").write_text(
            f"""export default function Home() {{
  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>UAI Engine Generated Site</h1>
      <p>Generated from prompt: {prompt[:100]}...</p>
      <div style={{ marginTop: '2rem', padding: '1rem', background: '#f0f0f0', borderRadius: '8px' }}>
        <h2>Welcome</h2>
        <p>This is a generated Next.js application.</p>
      </div>
    </div>
  )
}}
"""
        )
        
        (project_path / "next.config.js").write_text(
            """module.exports = {
  output: 'standalone',
}
"""
        )
        
        (project_path / "tsconfig.json").write_text(
            """{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
"""
        )

    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile for Next.js build using node:20-alpine."""
        return """FROM node:20-alpine AS base

# Install dependencies
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json ./
RUN npm install

# Build
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT 3000
CMD ["node", "server.js"]
"""

    async def _update_build_status(
        self,
        build_id: int,
        status: str,
        logs: str = None,
        preview_url: str = None,
        error_message: str = None,
    ):
        """Update build status via API."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.api_url}/api/v1/builds/{build_id}/status",
                    json={
                        "status": status,
                        "logs": logs,
                        "preview_url": preview_url,
                        "error_message": error_message,
                    },
                    timeout=30.0,
                )
        except Exception as e:
            logger.error("failed_to_update_build_status", build_id=build_id, error=str(e))
