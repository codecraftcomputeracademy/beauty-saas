import asyncio

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.organization.repositories.organization_repository import (
    OrganizationRepository,
)


async def main():
    async with AsyncSessionLocal() as session:
        repository = OrganizationRepository(session)

        # 1. Exact hostname lookup
        organization = await repository.get_by_hostname(
            "test-beauty.localhost"
        )

        assert organization is not None
        assert organization.hostname == "test-beauty.localhost"

        print("PASS: hostname lookup")

        # 2. Normalization: uppercase + whitespace
        organization = await repository.get_by_hostname(
            "  TEST-BEAUTY.LOCALHOST  "
        )

        assert organization is not None
        assert organization.hostname == "test-beauty.localhost"

        print("PASS: hostname normalization")

        # 3. Unknown hostname
        organization = await repository.get_by_hostname(
            "unknown-beauty.localhost"
        )

        assert organization is None

        print("PASS: unknown hostname")

        # 4. Lookup by ID
        organization = await repository.get_by_hostname(
            "test-beauty.localhost"
        )

        assert organization is not None

        organization_by_id = await repository.get_by_id(
            organization.id
        )

        assert organization_by_id is not None
        assert organization_by_id.id == organization.id

        print("PASS: organization ID lookup")

    print("\nAll OrganizationRepository tests passed.")


asyncio.run(main())