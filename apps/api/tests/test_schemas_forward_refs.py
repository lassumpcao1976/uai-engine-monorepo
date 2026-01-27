"""
Regression test to ensure forward references in schemas are properly resolved.
This prevents the "name 'UserResponse' is not defined" error.
"""
import pytest
from schemas import AuthResponse, UserResponse, ProjectResponse, VersionResponse, BuildResponse


def test_user_response_defined():
    """Test that UserResponse can be instantiated"""
    user = UserResponse(
        id="test-id",
        email="test@example.com",
        name="Test User",
        role="free",
        credits=100.0
    )
    assert user.id == "test-id"
    assert user.email == "test@example.com"


def test_auth_response_with_user():
    """Test that AuthResponse can reference UserResponse without forward ref errors"""
    user = UserResponse(
        id="test-id",
        email="test@example.com",
        name="Test User",
        role="free",
        credits=100.0
    )
    auth = AuthResponse(
        access_token="test-token",
        token_type="bearer",
        user=user
    )
    assert auth.access_token == "test-token"
    assert auth.user.id == "test-id"


def test_project_response_forward_refs():
    """Test that ProjectResponse can reference VersionResponse and BuildResponse"""
    build = BuildResponse(
        id="build-id",
        project_id="project-id",
        version_id="version-id",
        status="success",
        attempt_number=1,
        build_logs=None,
        error_message=None,
        lint_output=None,
        build_output=None,
        preview_url=None,
        created_at="2024-01-01T00:00:00",
        completed_at=None
    )
    version = VersionResponse(
        id="version-id",
        project_id="project-id",
        version_number=1,
        spec_snapshot={},
        code_diff=None,
        created_at="2024-01-01T00:00:00",
        created_by=None,
        build=build
    )
    project = ProjectResponse(
        id="project-id",
        user_id="user-id",
        name="Test Project",
        description=None,
        initial_prompt="Test prompt",
        status="active",
        preview_url=None,
        published_url=None,
        watermark_enabled=True,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        latest_version=version,
        latest_build=build
    )
    assert project.latest_version is not None
    assert project.latest_build is not None
