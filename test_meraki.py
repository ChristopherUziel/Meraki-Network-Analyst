import asyncio

from app.meraki_client import MerakiAPIError, MerakiClient


async def main() -> None:
    client = MerakiClient()

    try:
        organizations = await client.get_organizations()

        print(f"Organizaciones encontradas: {len(organizations)}")

        for organization in organizations:
            organization_id = organization.get("id")
            organization_name = organization.get("name")

            print(
                f"- {organization_name} "
                f"(ID: {organization_id})"
            )

    except MerakiAPIError as error:
        print(
            f"Error de Meraki {error.status_code}: "
            f"{error.detail}"
        )


if __name__ == "__main__":
    asyncio.run(main())