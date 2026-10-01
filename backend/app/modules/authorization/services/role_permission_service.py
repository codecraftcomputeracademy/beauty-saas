from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.authorization.models.permission import Permission
from app.modules.authorization.models.role import Role
from app.modules.authorization.models.role_permission import RolePermission


class RolePermissionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> RolePermission:
        role_result = await self.session.execute(
            select(Role).where(
                Role.id == role_id,
            )
        )

        role = role_result.scalar_one_or_none()

        if role is None:
            raise ValueError("Role not found")

        if role.status != "ACTIVE":
            raise ValueError("Role is inactive")

        permission_result = await self.session.execute(
            select(Permission).where(
                Permission.id == permission_id,
            )
        )

        permission = permission_result.scalar_one_or_none()

        if permission is None:
            raise ValueError("Permission not found")

        if permission.status != "ACTIVE":
            raise ValueError("Permission is inactive")

        existing_result = await self.session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )

        if existing_result.scalar_one_or_none() is not None:
            raise ValueError(
                "Permission is already assigned to this role"
            )

        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
        )

        self.session.add(role_permission)

        await self.session.flush()

        return role_permission

    async def remove_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        result = await self.session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )

        role_permission = result.scalar_one_or_none()

        if role_permission is None:
            raise ValueError(
                "Permission is not assigned to this role"
            )

        await self.session.delete(role_permission)

        await self.session.flush()