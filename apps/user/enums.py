from enum import Enum


class TokenType(str, Enum):
    ACCESS: str = "access"
    REFRESH: str = "refresh"
