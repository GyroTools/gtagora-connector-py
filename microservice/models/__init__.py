from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
import re


class ScriptExecutionRequest(BaseModel):
    """Request model for script execution."""

    script: str = Field(
        ...,
        description="The script content to execute",
        min_length=1,
        max_length=100000
    )
    timeout: Optional[int] = Field(
        default=30,
        description="Timeout for script execution in seconds",
        ge=1,
        le=300
    )
    environment_variables: Optional[Dict[str, str]] = Field(
        default=None,
        description="Environment variables to set for script execution"
    )
    working_directory: Optional[str] = Field(
        default=None,
        description="Working directory for script execution"
    )

    @field_validator('script')
    @classmethod
    def validate_script(cls, v: str) -> str:
        """Validate script content for basic security."""
        if not v.strip():
            raise ValueError("Script content cannot be empty")

        # Basic security check - prevent dangerous commands
        dangerous_patterns = [
            r'\brm\s+-rf\s+/',
            r'\bformat\s+C:',
            r'\bdel\s+/[fs]',
            r'>\s*/dev/sd[a-z]',
            r'\bdd\s+if=.*of=/dev/',
            r'\bmkfs\.',
            r'\bfdisk\b',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Script contains potentially dangerous command: {pattern}")

        return v

    @field_validator('environment_variables')
    @classmethod
    def validate_environment_variables(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Validate environment variables."""
        if v is None:
            return v

        if len(v) > 50:
            raise ValueError("Too many environment variables (max 50)")

        for key, value in v.items():
            if len(key) > 100 or len(value) > 1000:
                raise ValueError("Environment variable key/value too long")

            # Basic validation for key names
            if not re.match(r'^[A-Z_][A-Z0-9_]*$', key):
                raise ValueError(f"Invalid environment variable name: {key}")

        return v


class ScriptExecutionResponse(BaseModel):
    """Response model for script execution."""

    success: bool = Field(
        ...,
        description="Whether the script executed successfully"
    )
    exit_code: int = Field(
        ...,
        description="Exit code of the script execution"
    )
    stdout: str = Field(
        ...,
        description="Standard output from script execution"
    )
    stderr: str = Field(
        ...,
        description="Standard error from script execution"
    )
    execution_time: float = Field(
        ...,
        description="Time taken for script execution in seconds"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(
        ...,
        description="Service status"
    )
    version: str = Field(
        ...,
        description="Service version"
    )
    timestamp: str = Field(
        ...,
        description="Current timestamp"
    )
