from typing import Any

import httpx

from app.settings import get_settings


class MerakiAPIError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class MerakiClient:
    def __init__(self) -> None:
        settings = get_settings()

        self.base_url = settings.meraki_base_url.rstrip("/")
        self.headers = {
            "X-Cisco-Meraki-API-Key": settings.meraki_api_key,
            "Accept": "application/json",
            "User-Agent": "Meraki-Copilot-Agent/0.1",
        }

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
        ) as client:
            response = await client.get(url, params=params)

        if response.status_code >= 400:
            raise MerakiAPIError(
                status_code=response.status_code,
                detail=self._get_safe_error(response),
            )

        return response.json()

    @staticmethod
    def _get_safe_error(response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return "Meraki devolvió una respuesta no válida."

        if isinstance(body, dict):
            errors = body.get("errors")

            if isinstance(errors, list):
                return "; ".join(str(error) for error in errors)

        return str(body)

    async def get_organizations(self) -> list[dict[str, Any]]:
        return await self.get("/organizations")

    async def get_device_status_overview(
        self,
        organization_id: str,
    ) -> dict[str, Any]:
        path = (
            f"/organizations/{organization_id}"
            "/devices/statuses/overview"
        )

        return await self.get(path)