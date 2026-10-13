import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.settings import get_settings

bridge_api_key_header = APIKeyHeader(
    name="X-Bridge-API-Key",
    scheme_name="BridgeApiKey",
    description=(
        "Clave utilizada por Copilot Studio para acceder a los endpoints protegidos."
    ),
    auto_error=False,
)


async def require_bridge_api_key(
    provided_api_key: str | None = Security(bridge_api_key_header),
) -> None:
    settings = get_settings()

    if provided_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta la clave de acceso del Bridge.",
        )

    if not secrets.compare_digest(
        provided_api_key,
        settings.bridge_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La clave de acceso del Bridge no es válida.",
        )
