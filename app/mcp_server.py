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


@mcp.tool()
async def list_organization_networks(
    organization_id: str,
) -> dict[str, Any]:
    """Lista las redes Cisco Meraki de una organización.

    Utiliza esta herramienta cuando el usuario pregunte qué redes,
    sitios, sucursales o ubicaciones existen dentro de una organización.

    Si el usuario solo proporciona el nombre de la organización,
    utiliza primero list_meraki_organizations para obtener su ID.

    Args:
        organization_id: Identificador único de la organización Meraki.

    Esta herramienta es estrictamente de solo lectura.
    """
    client = MerakiClient()

    try:
        networks = await client.get_organization_networks(organization_id)
    except MerakiAPIError as error:
        return {
            "success": False,
            "organizationId": organization_id,
            "error": {
                "statusCode": error.status_code,
                "detail": error.detail,
            },
        }

    sanitized_networks = [
        {
            "id": network.get("id"),
            "organizationId": network.get("organizationId"),
            "name": network.get("name"),
            "productTypes": network.get("productTypes"),
            "timeZone": network.get("timeZone"),
            "tags": network.get("tags"),
            "enrollmentString": network.get("enrollmentString"),
            "url": network.get("url"),
            "notes": network.get("notes"),
            "isBoundToConfigTemplate": network.get("isBoundToConfigTemplate"),
        }
        for network in networks
    ]

    return {
        "success": True,
        "organizationId": organization_id,
        "count": len(sanitized_networks),
        "networks": sanitized_networks,
    }


@mcp.tool()
async def list_organization_devices(
    organization_id: str,
    network_id: str | None = None,
    product_type: str | None = None,
) -> dict[str, Any]:
    """Lista los dispositivos asignados a redes de una organización.

    Utiliza esta herramienta para consultar inventario, nombres, modelos,
    seriales, direcciones MAC, tipos de equipos y redes asignadas.

    Puede filtrar por una red o por tipo de producto. Ejemplos de tipos
    válidos incluyen wireless, switch, appliance, camera, sensor y
    cellularGateway.

    Args:
        organization_id: Identificador único de la organización Meraki.
        network_id: Identificador opcional de una red específica.
        product_type: Tipo opcional de producto Meraki.

    Esta herramienta es estrictamente de solo lectura.
    """
    client = MerakiClient()

    try:
        devices = await client.get_organization_devices(
            organization_id=organization_id,
            network_id=network_id,
            product_type=product_type,
        )
    except MerakiAPIError as error:
        return {
            "success": False,
            "organizationId": organization_id,
            "error": {
                "statusCode": error.status_code,
                "detail": error.detail,
            },
        }

    sanitized_devices = [
        {
            "name": device.get("name"),
            "serial": device.get("serial"),
            "mac": device.get("mac"),
            "model": device.get("model"),
            "networkId": device.get("networkId"),
            "productType": device.get("productType"),
            "firmware": device.get("firmware"),
            "address": device.get("address"),
            "tags": device.get("tags"),
            "notes": device.get("notes"),
            "lanIp": device.get("lanIp"),
        }
        for device in devices
    ]

    return {
        "success": True,
        "organizationId": organization_id,
        "networkId": network_id,
        "productType": product_type,
        "count": len(sanitized_devices),
        "devices": sanitized_devices,
    }


@mcp.tool()
async def get_organization_device_availabilities(
    organization_id: str,
    network_id: str | None = None,
    product_type: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Consulta la disponibilidad actual de dispositivos Meraki.

    Utiliza esta herramienta para identificar dispositivos online,
    alerting, offline o dormant, y para responder qué APs, switches,
    appliances u otros dispositivos requieren atención.

    Puede filtrar por red, tipo de producto o estado. Los tipos comunes
    son wireless, switch, appliance, camera, sensor y cellularGateway.

    Args:
        organization_id: Identificador nico de la organización Meraki.
        network_id: Identificador opcional de una red.
        product_type: Tipo opcional de producto.
        status: Estado opcional, por ejemplo online, alerting, offline
            o dormant.

    Esta herramienta es estrictamente de solo lectura.
    """
    client = MerakiClient()

    try:
        availabilities = await client.get_device_availabilities(
            organization_id=organization_id,
            network_id=network_id,
            product_type=product_type,
            status=status,
        )
    except MerakiAPIError as error:
        return {
            "success": False,
            "organizationId": organization_id,
            "error": {
                "statusCode": error.status_code,
                "detail": error.detail,
            },
        }

    status_counts: dict[str, int] = {}

    for device in availabilities:
        device_status = device.get("status", "unknown")
        status_counts[device_status] = status_counts.get(device_status, 0) + 1

    sanitized_availabilities = [
        {
            "name": device.get("name"),
            "serial": device.get("serial"),
            "mac": device.get("mac"),
            "networkId": device.get("networkId"),
            "productType": device.get("productType"),
            "model": device.get("model"),
            "status": device.get("status"),
            "lastReportedAt": device.get("lastReportedAt"),
        }
        for device in availabilities
    ]

    return {
        "success": True,
        "organizationId": organization_id,
        "networkId": network_id,
        "productType": product_type,
        "statusFilter": status,
        "count": len(sanitized_availabilities),
        "statusCounts": status_counts,
        "devices": sanitized_availabilities,
        "dataFreshness": (
            "Cisco Meraki actualiza estos datos aproximadamente " "cada cinco minutos."
        ),
    }
