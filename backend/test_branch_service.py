import asyncio

import app.model_registry  # noqa: F401

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.modules.catalog.models.branch_service import BranchService


async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BranchService)
        )

        branch_services = result.scalars().all()

        for branch_service in branch_services:
            print(
                f"id={branch_service.id} | "
                f"org={branch_service.organization_id} | "
                f"branch={branch_service.branch_id} | "
                f"service={branch_service.service_id} | "
                f"price={branch_service.price} | "
                f"status={branch_service.status}"
            )


if __name__ == "__main__":
    asyncio.run(main())