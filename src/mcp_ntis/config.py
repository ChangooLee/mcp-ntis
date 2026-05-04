import os
from dataclasses import dataclass
from typing import Literal, cast

from dotenv import load_dotenv

load_dotenv()


@dataclass
class NTISConfig:
    api_key: str
    org_cd: str = ""
    user_id: str = ""
    cache_ttl_hours: int = 24

    @classmethod
    def from_env(cls) -> "NTISConfig":
        api_key = os.getenv("NTIS_API_KEY")
        if not api_key:
            raise ValueError("NTIS_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return cls(
            api_key=api_key,
            org_cd=os.getenv("NTIS_ORG_CD", ""),
            user_id=os.getenv("NTIS_USER_ID", ""),
            cache_ttl_hours=int(os.getenv("NTIS_CACHE_TTL_HOURS", "24")),
        )


@dataclass
class MCPConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    server_name: str = "mcp-ntis"
    transport: Literal["stdio", "http"] = "stdio"

    @classmethod
    def from_env(cls) -> "MCPConfig":
        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            server_name=os.getenv("MCP_SERVER_NAME", "mcp-ntis"),
            transport=cast(Literal["stdio", "http"], os.getenv("TRANSPORT", "stdio")),
        )
