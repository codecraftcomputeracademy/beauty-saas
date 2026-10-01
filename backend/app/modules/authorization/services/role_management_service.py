from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.authorization.models.role import Role
from app.modules.organization.models.organization import Organization


class RoleManagementService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_role(
        self,
        organization_id: UUID,
        code: str,
        name: str,
        description: str | None = None,
    ) -> Role:
        code = code.strip().upper()
        name = name.strip()

        if not code:
            raise ValueError("Role code is required")

        if not name:
            raise ValueError("Role name is required")

        organization_result = await self.session.execute(
            select(Organization.id).where(
                Organization.id == organization_id,
            )
        )

        if organization_result.scalar_one_or_none() is None:
            raise ValueError("Organization not found")

        existing_code_result = await self.session.execute(
            select(Role.id).where(
                Role.organization_id == organization_id,
                Role.code == code,
            )
        )

        if existing_code_result.scalar_one_or_none() is not None:
            raise ValueError(
                "Role code already exists in this organization"
            )

        existing_name_result = await self.session.execute(
            select(Role.id).where(
                Role.organization_id == organization_id,
                Role.name == name,
            )
        )

        if existing_name_result.scalar_one_or_none() is not None:
            raise ValueError(
                "Role name already exists in this organization"
            )

        role = Role(
            organization_id=organization_id,
            code=code,
            name=name,
            description=description,
            role_type="CUSTOM",
            status="ACTIVE",
        )

        self.session.add(role)

        await self.session.flush()

        return role