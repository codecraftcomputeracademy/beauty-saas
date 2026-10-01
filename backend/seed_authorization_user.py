import asyncio
from uuid import UUID

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.identity.services.user_management_service import (
    UserManagementService,
)


ORG_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")


async def main():
    async with AsyncSessionLocal() as session:
        service = UserManagementService(session)

        user = await service.create_user(
            organization_id=ORG_ID,
            username="authorization_test_user",
            password="Test@12345",
            email="authorization@test.local",
            first_name="Authorization",
            last_name="Tester",
            display_name="Authorization Tester",
        )

        await session.commit()

        print("Authorization test user created")
        print(f"ID: {user.id}")
        print(f"Organization ID: {user.organization_id}")
        print(f"Username: {user.username}")
        print(f"Status: {user.status}")


if __name__ == "__main__":
    asyncio.run(main())