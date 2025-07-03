# Script Execution Microservice

A secure FastAPI-based microservice for executing scripts remotely with comprehensive security measures and monitoring capabilities.

## Overview

This microservice provides a REST API endpoint that accepts scripts as input and executes them securely in a sandboxed environment. It's designed to be part of the gtagora-connector-py ecosystem and includes robust security features to prevent malicious script execution.

## Features

### Core Functionality
- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Secure Script Execution**: Uses subprocess with security restrictions
- **Input Validation**: Comprehensive validation using Pydantic models
- **Resource Limits**: CPU, memory, and time constraints
- **Output Sanitization**: Removes potentially sensitive information from outputs
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

### Security Features
- **Input Sanitization**: Validates and sanitizes script content
- **Dangerous Command Detection**: Blocks potentially harmful commands
- **Resource Limiting**: Prevents resource exhaustion attacks
- **Sandboxed Execution**: Isolates script execution from the host system
- **Timeout Protection**: Prevents long-running or infinite scripts
- **Output Truncation**: Limits output size to prevent memory exhaustion
- **Working Directory Validation**: Prevents access to sensitive directories

## API Endpoints

### `POST /execute-script`
Execute a script securely.

**Request Body:**
```json
{
  "script": "echo 'Hello, World!'",
  "timeout": 30,
  "environment_variables": {
    "MY_VAR": "value"
  },
  "working_directory": "/tmp"
}
```

**Response:**
```json
{
  "success": true,
  "exit_code": 0,
  "stdout": "Hello, World!\n",
  "stderr": "",
  "execution_time": 0.123,
  "error_message": null
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### `GET /api/info`
Get API information and available endpoints.

### `GET /docs`
Interactive API documentation (Swagger UI).

### `GET /redoc`
Alternative API documentation (ReDoc).

## Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Service:**
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Configuration

The service can be configured using environment variables:

- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8000)
- `WORKERS`: Number of worker processes (default: 1)
- `LOG_LEVEL`: Logging level (default: "INFO")
- `LOG_FILE`: Optional log file path
- `RELOAD`: Enable auto-reload during development (default: "false")

## Usage Examples

### Basic Script Execution
```bash
curl -X POST "http://localhost:8000/execute-script" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "echo \"Current date: $(date)\"",
    "timeout": 10
  }'
```

### Script with Environment Variables
```bash
curl -X POST "http://localhost:8000/execute-script" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "echo \"Hello, $NAME!\"",
    "timeout": 10,
    "environment_variables": {
      "NAME": "World"
    }
  }'
```

### Python Script Example
```bash
curl -X POST "http://localhost:8000/execute-script" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "python3 -c \"import sys; print(f'Python version: {sys.version}')\"",
    "timeout": 15
  }'
```

## Security Considerations

### Input Validation
- Script content is validated for dangerous patterns
- Maximum script length: 100,000 characters
- Environment variable validation
- Working directory path validation

### Execution Security
- Scripts run in a sandboxed environment
- Resource limits prevent system abuse
- Timeout protection prevents infinite execution
- Output sanitization removes sensitive information

### Blocked Commands
The service blocks potentially dangerous commands including:
- `rm -rf /`
- `format C:`
- `dd` operations to system devices
- `mkfs` filesystem operations
- `fdisk` disk operations
- Fork bombs and infinite loops

## Monitoring and Logging

The service provides comprehensive logging including:
- Script execution requests
- Security violations
- Performance metrics
- Error conditions
- Resource usage

Logs are structured and can be configured to output to console and/or file.

## Error Handling

The service includes comprehensive error handling:
- Input validation errors (400 Bad Request)
- Script execution failures (returned in response)
- Internal server errors (500 Internal Server Error)
- Service unavailable errors (503 Service Unavailable)

## Testing

Test the service using the provided endpoints:

1. **Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Simple Script:**
   ```bash
   curl -X POST "http://localhost:8000/execute-script" \
     -H "Content-Type: application/json" \
     -d '{"script": "echo \"Test successful\"", "timeout": 5}'
   ```

3. **API Documentation:**
   Open http://localhost:8000/docs in your browser

## Development

### Running in Development Mode
```bash
RELOAD=true python main.py
```

### Running with Debug Logging
```bash
LOG_LEVEL=DEBUG python main.py
```

### Docker Support
```bash
# Build Docker image
docker build -t script-execution-microservice .

# Run container
docker run -p 8000:8000 script-execution-microservice
```

## Production Deployment

For production deployment, consider:

1. **Security:**
   - Configure CORS appropriately
   - Use HTTPS/TLS
   - Implement authentication/authorization
   - Run with non-root user

2. **Performance:**
   - Use multiple worker processes
   - Configure appropriate resource limits
   - Monitor resource usage

3. **Monitoring:**
   - Set up log aggregation
   - Configure health checks
   - Monitor API metrics

## License

This microservice is part of the gtagora-connector-py project and is licensed under the MIT License.

## Support

For issues and questions, please refer to the main gtagora-connector-py repository documentation and issue tracker.