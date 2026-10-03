from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organization.models.organization import Organization
from app.modules.organization.repositories.organization_repository import (
    OrganizationRepository,
)


class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.repository = OrganizationRepository(session)

    async def get_by_id(
        self,
        organization_id: UUID,
    ) -> Organization | None:
        return await self.repository.get_by_id(
            organization_id
        )

    async def get_by_hostname(
        self,
        hostname: str,
    ) -> Organization | None:
        return await self.repository.get_by_hostname(
            hostname
        )