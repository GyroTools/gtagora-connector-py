import logging
import sys
from datetime import datetime, timezone
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the microservice.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("script_execution_service")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        Current timestamp as ISO string
    """
    return datetime.now(timezone.utc).isoformat()


def sanitize_output(output: str, max_length: int = 10000) -> str:
    """
    Sanitize output by removing potentially sensitive information and limiting length.

    Args:
        output: Raw output string
        max_length: Maximum allowed length

    Returns:
        Sanitized output string
    """
    if not output:
        return ""

    # Remove potential sensitive patterns
    import re

    # Remove potential file paths that might contain sensitive info
    sanitized = re.sub(r'/home/[^/\s]+', '/home/[user]', output)
    sanitized = re.sub(r'/Users/[^/\s]+', '/Users/[user]', sanitized)

    # Remove potential API keys or tokens (basic patterns)
    sanitized = re.sub(r'(api[_-]?key|token|password|secret)[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9_-]+',
                       r'\1=***', sanitized, flags=re.IGNORECASE)

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "\n... (output truncated for security)"

    return sanitized


def validate_script_safety(script: str) -> bool:
    """
    Perform basic safety validation on script content.

    Args:
        script: Script content to validate

    Returns:
        True if script appears safe, False otherwise
    """
    import re

    # List of dangerous patterns
    dangerous_patterns = [
        r'\brm\s+-rf\s*/',
        r'\bformat\s+[a-zA-Z]:',
        r'\bdel\s+/[fs]',
        r'>\s*/dev/sd[a-z]',
        r'\bdd\s+if=.*of=/dev/',
        r'\bmkfs\.',
        r'\bfdisk\b',
        r'\bsudo\s+rm',
        r'\bsudo\s+dd',
        r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;?\s*:',  # fork bomb
        r'while\s*\[\s*1\s*\].*do.*done',  # infinite loop
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, script, re.IGNORECASE | re.MULTILINE):
            return False

    return True
