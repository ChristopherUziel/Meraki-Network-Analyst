from typing import Any

from mcp.server import MCPServer

from app.meraki_client import MerakiAPIError, MerakiClient

mcp = MCPServer("Meraki Network Analyst")


@mcp.tool()
async def list_meraki_organizations() -> dict[str, Any]:
    """Obtiene las organizaciones Cisco Meraki disponibles.

    Utiliza esta herramienta cuando el usuario quiera conocer, listar,
    identificar o seleccionar una organización Meraki. También debe
    utilizarse cuando otra herramienta requiera organization_id y el
    usuario solamente haya proporcionado el nombre de la organización.

    Esta herramienta es estrictamente de solo lectura.
    """
    client = MerakiClient()

    try:
        organizations = await client.get_organizations()
    except MerakiAPIError as error:
        return {
            "success": False,
            "error": {
                "statusCode": error.status_code,
                "detail": error.detail,
            },
        }

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
        "success": True,
        "count": len(sanitized_organizations),
        "organizations": sanitized_organizations,
    }


@mcp.tool()
async def get_organization_device_status_overview(
    organization_id: str,
) -> dict[str, Any]:
    """Obtiene el resumen actual del estado de dispositivos Meraki.

    Utiliza esta herramienta cuando el usuario pregunte por la salud
    neral, disponibilidad o cantidad de dispositivos online, alerting,
    offline o dormant de una organización Cisco Meraki.

    Si el usuario proporciona el nombre de la organización, pero no el
    organization_id, utiliza primero list_meraki_organizations.

    Args:
        organization_id: Identificador único de la organización Meraki.

    Esta herramienta es estrictamente de solo lectura.
    """
    client = MerakiClient()

    try:
        overview = await client.get_device_status_overview(organization_id)
    except MerakiAPIError as error:
        return {
            "success": False,
            "organizationId": organization_id,
            "error": {
                "statusCode": error.status_code,
                "detail": error.detail,
            },
        }

    return {
        "success": True,
        "organizationId": organization_id,
        "statusOverview": overview,
    }
