from fastapi import Depends, FastAPI, HTTPException, Path

from app.meraki_client import MerakiAPIError, MerakiClient

# importacion validacion de seguridad
from app.security import require_bridge_api_key

from contextlib import AsyncExitStack, asynccontextmanager
from app.mcp_server import mcp

# Proteger mcp
import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.settings import get_settings

# Configurar hostname permitido
from mcp.server.transport_security import TransportSecuritySettings


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield


app = FastAPI(
    title="Meraki Copilot API",
    description=(
        "API de solo lectura para conectar Microsoft 365 Copilot " "con Cisco Meraki."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


class MCPApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            provided_key = request.headers.get("X-Bridge-API-Key")
            expected_key = get_settings().bridge_api_key

            if provided_key is None or not secrets.compare_digest(
                provided_key,
                expected_key,
            ):
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": ("La clave de acceso del Bridge " "no es válida.")
                    },
                )

        return await call_next(request)


app.add_middleware(MCPApiKeyMiddleware)


@app.get(
    "/health",
    operation_id="getApiHealth",
    summary="Comprueba la disponibilidad de la API",
)
async def get_health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "Meraki Copilot API",
        "version": "0.1.0",
    }


@app.get(
    "/organizations",
    operation_id="getOrganizations",
    summary="Obtiene las organizaciones disponibles en Meraki",
    dependencies=[Depends(require_bridge_api_key)],
)
async def get_organizations() -> dict:
    client = MerakiClient()

    try:
        organizations = await client.get_organizations()

        sanitized_organizations = [
            {
                "id": organization.get("id"),
                "name": organization.get("name"),
                "url": organization.get("url"),
                "api": organization.get("api"),
                "licensing": organization.get("licensing"),
            }
            for organization in organizations
        ]

        return {
            "count": len(sanitized_organizations),
            "organizations": sanitized_organizations,
        }

    except MerakiAPIError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        ) from error


@app.get(
    "/organizations/{organization_id}/device-status-overview",
    operation_id="getOrganizationDeviceStatusOverview",
    summary="Obtiene el resumen del estado de los dispositivos",
    dependencies=[Depends(require_bridge_api_key)],
)
async def get_organization_device_status_overview(
    organization_id: str = Path(
        min_length=1,
        description="Identificador de la organización de Meraki",
    ),
) -> dict:
    client = MerakiClient()

    try:
        status_overview = await client.get_device_status_overview(organization_id)

        return {
            "organizationId": organization_id,
            "statusOverview": status_overview,
        }

    except MerakiAPIError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        ) from error


mcp_transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[
        "127.0.0.1:8000",
        "localhost:8000",
        "tkfvsm4p-8000.usw3.devtunnels.ms",
    ],
)

app.mount(
    "/",
    mcp.streamable_http_app(
        transport_security=mcp_transport_security,
    ),
)
