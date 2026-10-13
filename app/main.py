from fastapi import Depends, FastAPI, HTTPException, Path

from app.meraki_client import MerakiAPIError, MerakiClient
#importacion validacion de seguridad
from app.security import require_bridge_api_key


app = FastAPI(
    title="Meraki Copilot API",
    description=(
        "API de solo lectura para conectar Microsoft 365 Copilot "
        "con Cisco Meraki."
    ),
    version="0.1.0",
)


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
        status_overview = await client.get_device_status_overview(
            organization_id
        )

        return {
            "organizationId": organization_id,
            "statusOverview": status_overview,
        }

    except MerakiAPIError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        ) from error