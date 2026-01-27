"""
Log sanitization service to redact secrets
"""
import re
from typing import List


# Common secret patterns
SECRET_PATTERNS = [
    r'password["\s:=]+([^\s"\']+)',
    r'api[_-]?key["\s:=]+([^\s"\']+)',
    r'secret["\s:=]+([^\s"\']+)',
    r'token["\s:=]+([^\s"\']+)',
    r'jwt[_-]?secret["\s:=]+([^\s"\']+)',
    r'private[_-]?key["\s:=]+([^\s"\']+)',
    r'access[_-]?token["\s:=]+([^\s"\']+)',
    r'authorization["\s:=]+([^\s"\']+)',
]


def sanitize_logs(logs: str) -> str:
    """
    Redact secrets from logs.
    Returns sanitized log string.
    """
    sanitized = logs
    
    for pattern in SECRET_PATTERNS:
        # Replace matched secrets with [REDACTED]
        sanitized = re.sub(
            pattern,
            lambda m: m.group(0).split('=')[0] + '=[REDACTED]' if '=' in m.group(0) else '[REDACTED]',
            sanitized,
            flags=re.IGNORECASE
        )
    
    # Also redact common JWT tokens (long base64 strings)
    jwt_pattern = r'Bearer\s+([A-Za-z0-9_-]{20,})'
    sanitized = re.sub(jwt_pattern, 'Bearer [REDACTED]', sanitized)
    
    return sanitized
