import pytest
from fastapi.testclient import TestClient
import sys
import os

# Import the FastAPI app - needs to be after path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app  # noqa: E402

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and info endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns health status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

    def test_api_info_endpoint(self):
        """Test API info endpoint."""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "endpoints" in data
        assert "security_features" in data


class TestScriptExecution:
    """Test script execution endpoint."""

    def test_simple_echo_script(self):
        """Test executing a simple echo script."""
        request_data = {
            "script": "echo 'Hello, World!'",
            "timeout": 10
        }

        response = client.post("/execute-script", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert "Hello, World!" in data["stdout"]
        assert data["stderr"] == ""
        assert data["execution_time"] > 0
        assert data["error_message"] is None

    def test_script_with_environment_variables(self):
        """Test script execution with environment variables."""
        request_data = {
            "script": "echo \"Hello, $TEST_VAR!\"",
            "timeout": 10,
            "environment_variables": {
                "TEST_VAR": "FastAPI"
            }
        }

        response = client.post("/execute-script", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert "Hello, FastAPI!" in data["stdout"]

    def test_script_with_non_zero_exit_code(self):
        """Test script that exits with non-zero code."""
        request_data = {
            "script": "exit 1",
            "timeout": 10
        }

        response = client.post("/execute-script", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is False
        assert data["exit_code"] == 1

    def test_invalid_script_validation(self):
        """Test script validation for dangerous commands."""
        request_data = {
            "script": "rm -rf /",
            "timeout": 10
        }

        response = client.post("/execute-script", json=request_data)
        assert response.status_code == 400
        assert "dangerous commands" in response.json()["detail"]

    def test_empty_script_validation(self):
        """Test validation of empty script."""
        request_data = {
            "script": "",
            "timeout": 10
        }

        response = client.post("/execute-script", json=request_data)
        assert response.status_code == 422  # Pydantic validation error

    def test_script_timeout_validation(self):
        """Test timeout parameter validation."""
        # Test timeout too large
        request_data = {
            "script": "echo 'test'",
            "timeout": 400  # > 300 max
        }

        response = client.post("/execute-script", json=request_data)
        assert response.status_code == 422  # Pydantic validation error

        # Test timeout too small
        request_data = {
            "script": "echo 'test'",
            "timeout": 0
        }

        response = client.post("/execute-script", json=request_data)
        assert response.status_code == 422  # Pydantic validation error

    def test_environment_variables_validation(self):
        """Test environment variables validation."""
        # Test invalid environment variable name
        request_data = {
            "script": "echo 'test'",
            "timeout": 10,
            "environment_variables": {
                "invalid-name": "value"
            }
        }

        response = client.post("/execute-script", json=request_data)
        assert response.status_code == 422  # Pydantic validation error


class TestSecurity:
    """Test security features."""

    def test_dangerous_command_blocking(self):
        """Test that dangerous commands are blocked."""
        dangerous_scripts = [
            "rm -rf /",
            "format C:",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
            "sudo rm -rf /home"
        ]

        for script in dangerous_scripts:
            request_data = {
                "script": script,
                "timeout": 10
            }

            response = client.post("/execute-script", json=request_data)
            # Should be blocked either by Pydantic validation or safety check
            assert response.status_code in [400, 422]

    def test_script_length_limit(self):
        """Test script length validation."""
        # Create a script that's too long (> 100,000 characters)
        long_script = "echo 'test'\n" * 10000  # Much longer than limit

        request_data = {
            "script": long_script,
            "timeout": 10
        }

        response = client.post("/execute-script", json=request_data)
        assert response.status_code == 422  # Pydantic validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
