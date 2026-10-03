import asyncio

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.organization.services.organization_service import (
    OrganizationService,
)


async def main():
    async with AsyncSessionLocal() as session:
        service = OrganizationService(session)

        organization = await service.get_by_hostname(
            "test-beauty.localhost"
        )

        assert organization is not None
        assert organization.hostname == "test-beauty.localhost"

        print("PASS: service hostname lookup")

        organization_by_id = await service.get_by_id(
            organization.id
        )

        assert organization_by_id is not None
        assert organization_by_id.id == organization.id

        print("PASS: service ID lookup")

        unknown = await service.get_by_hostname(
            "unknown-beauty.localhost"
        )

        assert unknown is None

        print("PASS: service unknown hostname")


asyncio.run(main())