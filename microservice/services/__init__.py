import subprocess
import time
import tempfile
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple

from models import ScriptExecutionRequest, ScriptExecutionResponse

logger = logging.getLogger(__name__)


class ScriptExecutionService:
    """Service for executing scripts securely."""

    def __init__(self):
        self.max_timeout = 300  # 5 minutes maximum
        self.default_timeout = 30

    async def execute_script(self, request: ScriptExecutionRequest) -> ScriptExecutionResponse:
        """
        Execute a script with security measures.

        Args:
            request: Script execution request containing script and parameters

        Returns:
            ScriptExecutionResponse with execution results
        """
        start_time = time.time()

        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                temp_file.write(request.script)
                temp_script_path = temp_file.name

            try:
                # Make script executable
                os.chmod(temp_script_path, 0o755)

                # Execute script
                stdout, stderr, exit_code = await self._run_script(
                    temp_script_path,
                    timeout=request.timeout or self.default_timeout,
                    env_vars=request.environment_variables,
                    working_dir=request.working_directory
                )

                execution_time = time.time() - start_time

                return ScriptExecutionResponse(
                    success=exit_code == 0,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    execution_time=execution_time,
                    error_message=stderr if exit_code != 0 else None
                )

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_script_path)
                except OSError:
                    logger.warning(f"Failed to delete temporary script file: {temp_script_path}")

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Script execution failed: {str(e)}")

            return ScriptExecutionResponse(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                execution_time=execution_time,
                error_message=f"Script execution failed: {str(e)}"
            )

    async def _run_script(
        self,
        script_path: str,
        timeout: int,
        env_vars: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        Run the script with security restrictions.

        Args:
            script_path: Path to the script file
            timeout: Timeout in seconds
            env_vars: Environment variables to set
            working_dir: Working directory for execution

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Validate working directory
        if working_dir:
            working_dir = self._validate_working_directory(working_dir)
        else:
            working_dir = tempfile.gettempdir()

        # Security: limit resource usage
        cmd = ['bash', script_path]

        try:
            logger.info(f"Executing script: {script_path} with timeout: {timeout}s")

            # Debug: log script content (first 100 chars)
            with open(script_path, 'r') as f:
                script_content = f.read()
                logger.info(f"Script content preview: {script_content[:100]}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=working_dir,
                text=True,
                # Security restrictions
                start_new_session=True,  # Prevent signal propagation
                preexec_fn=self._limit_resources if os.name != 'nt' else None,
                shell=False  # Important: don't use shell=True for security
            )

            stdout, stderr = process.communicate(timeout=timeout)  # Use Python's timeout
            exit_code = process.returncode

            # Truncate output if too large (security measure)
            max_output_size = 100000  # 100KB
            if len(stdout) > max_output_size:
                stdout = stdout[:max_output_size] + "\n... (output truncated)"
            if len(stderr) > max_output_size:
                stderr = stderr[:max_output_size] + "\n... (output truncated)"

            logger.info(f"Script execution completed with exit code: {exit_code}")

            return stdout, stderr, exit_code

        except subprocess.TimeoutExpired:
            logger.warning(f"Script execution timed out after {timeout} seconds")
            try:
                process.kill()
                process.wait()
            except Exception:
                pass
            return "", f"Script execution timed out after {timeout} seconds", 124

        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            return "", f"Error executing script: {str(e)}", -1

    def _validate_working_directory(self, working_dir: str) -> str:
        """
        Validate and sanitize working directory.

        Args:
            working_dir: Working directory path

        Returns:
            Validated working directory path
        """
        try:
            # Resolve path and check if it exists
            path = Path(working_dir).resolve()

            # Security: prevent access to sensitive directories
            sensitive_dirs = ['/etc', '/usr', '/bin', '/sbin', '/root', '/home']
            for sensitive in sensitive_dirs:
                if str(path).startswith(sensitive):
                    logger.warning(f"Access denied to sensitive directory: {path}")
                    return tempfile.gettempdir()

            if not path.exists():
                logger.warning(f"Working directory does not exist: {path}")
                return tempfile.gettempdir()

            if not path.is_dir():
                logger.warning(f"Working directory is not a directory: {path}")
                return tempfile.gettempdir()

            return str(path)

        except Exception as e:
            logger.warning(f"Invalid working directory: {working_dir}, error: {e}")
            return tempfile.gettempdir()

    def _limit_resources(self):
        """Limit resources for the subprocess (Unix only)."""
        import resource

        # Limit CPU time to prevent infinite loops
        resource.setrlimit(resource.RLIMIT_CPU, (300, 300))  # 5 minutes

        # Limit memory usage (if available)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))  # 512MB
        except Exception:
            pass  # Not all systems support memory limits

        # Limit number of processes
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))
        except Exception:
            pass
