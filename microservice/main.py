from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from contextlib import asynccontextmanager

from models import ScriptExecutionRequest, ScriptExecutionResponse, HealthResponse
from services import ScriptExecutionService
from utils import setup_logging, get_current_timestamp, sanitize_output, validate_script_safety

# Global service instance
script_service = None
logger = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global script_service, logger

    # Startup
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE")

    logger = setup_logging(log_level, log_file)
    script_service = ScriptExecutionService()

    logger.info("Script execution microservice started")
    yield

    # Shutdown
    logger.info("Script execution microservice shutting down")


# Create FastAPI app
app = FastAPI(
    title="Script Execution Microservice",
    description="A secure microservice for executing scripts remotely",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=get_current_timestamp()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=get_current_timestamp()
    )


async def get_script_service() -> ScriptExecutionService:
    """Dependency to get script service instance."""
    if script_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Script execution service not available"
        )
    return script_service


@app.post("/execute-script", response_model=ScriptExecutionResponse)
async def execute_script(
    request: ScriptExecutionRequest,
    service: ScriptExecutionService = Depends(get_script_service)
):
    """
    Execute a script securely.

    This endpoint accepts a script and executes it with security measures including:
    - Input validation and sanitization
    - Resource limits (CPU, memory, time)
    - Output sanitization
    - Sandboxed execution environment

    Args:
        request: Script execution request containing script and parameters
        service: Script execution service instance

    Returns:
        Script execution results including stdout, stderr, exit code, and execution time

    Raises:
        HTTPException: If script validation fails or execution encounters critical errors
    """
    try:
        # Additional safety validation
        if not validate_script_safety(request.script):
            logger.warning("Script failed safety validation")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Script contains potentially dangerous commands"
            )

        # Log the execution request (without script content for security)
        logger.info(f"Executing script with timeout: {request.timeout}s")

        # Execute the script
        response = await service.execute_script(request)

        # Sanitize output before returning
        response.stdout = sanitize_output(response.stdout)
        response.stderr = sanitize_output(response.stderr)

        # Log execution results
        logger.info(f"Script execution completed: success={response.success}, "
                    f"exit_code={response.exit_code}, time={response.execution_time:.2f}s")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in execute_script endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Script execution failed due to internal error"
        )


@app.get("/api/info")
async def get_api_info():
    """Get API information and available endpoints."""
    return {
        "service": "Script Execution Microservice",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "Health check and service info",
            "GET /health": "Health check endpoint",
            "POST /execute-script": "Execute a script securely",
            "GET /api/info": "API information",
            "GET /docs": "Interactive API documentation",
            "GET /redoc": "Alternative API documentation"
        },
        "security_features": [
            "Input validation and sanitization",
            "Resource limits (CPU, memory, time)",
            "Output sanitization",
            "Sandboxed execution environment",
            "Comprehensive logging"
        ]
    }


if __name__ == "__main__":
    import uvicorn

    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))

    # Run the application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )
