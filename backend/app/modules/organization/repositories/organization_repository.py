from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organization.models.organization import Organization


class OrganizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self,
        organization_id: UUID,
    ) -> Organization | None:
        result = await self.session.execute(
            select(Organization).where(
                Organization.id == organization_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_hostname(
        self,
        hostname: str,
    ) -> Organization | None:
        normalized_hostname = hostname.strip().lower()

        if not normalized_hostname:
            return None

        result = await self.session.execute(
            select(Organization).where(
                Organization.hostname == normalized_hostname,
            )
        )

        return result.scalar_one_or_none()