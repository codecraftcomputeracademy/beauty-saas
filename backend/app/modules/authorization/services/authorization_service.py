from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_

from app.modules.authorization.models.permission import Permission
from app.modules.authorization.models.role import Role
from app.modules.authorization.models.role_assignment import RoleAssignment
from app.modules.authorization.models.role_permission import RolePermission
from app.modules.identity.models.user import User
from app.modules.organization.models.branch import Branch


class AuthorizationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def has_permission(
        self,
        organization_id: UUID,
        user_id: UUID,
        permission_code: str,
        branch_id: UUID | None = None,
    ) -> bool:
        permission_code = permission_code.strip().upper()

        if not permission_code:
            return False

        # 1. User must belong to the requested organization.
        user_result = await self.session.execute(
            select(User.id).where(
                User.id == user_id,
                User.organization_id == organization_id,
                User.status == "ACTIVE",
            )
        )

        if user_result.scalar_one_or_none() is None:
            return False

        # 2. If a branch is supplied, it must belong to the organization.
        if branch_id is not None:
            branch_result = await self.session.execute(
                select(Branch.id).where(
                    Branch.id == branch_id,
                    Branch.organization_id == organization_id,
                )
            )

            if branch_result.scalar_one_or_none() is None:
                return False

        # 3. Permission must exist and be active.
        permission_result = await self.session.execute(
            select(Permission.id).where(
                Permission.code == permission_code,
                Permission.status == "ACTIVE",
            )
        )

        permission_id = permission_result.scalar_one_or_none()

        if permission_id is None:
            return False

        # 4. Find an applicable active role assignment.
        #
        # An organization-wide assignment (branch_id IS NULL)
        # applies to all branches in that organization.
        #
        # A branch-specific assignment applies only to that branch.
        assignment_query = (
            select(RoleAssignment.id)
               .join(
                Role,
                Role.id == RoleAssignment.role_id,
                )
                .join(
                    RolePermission,
                    RolePermission.role_id == Role.id,
                )
            .where(
            RoleAssignment.organization_id == organization_id,
            RoleAssignment.user_id == user_id,
            RoleAssignment.status == "ACTIVE",

            RoleAssignment.valid_from.is_(None)
            | (RoleAssignment.valid_from <= datetime.now(timezone.utc)),

            RoleAssignment.valid_until.is_(None)
            | (RoleAssignment.valid_until >= datetime.now(timezone.utc)),

            Role.status == "ACTIVE",
            RolePermission.permission_id == permission_id,

            # Tenant safety:
            # system roles are global definitions,
            # custom roles must belong to this organization.
            or_(
                Role.organization_id.is_(None),
                Role.organization_id == organization_id,
                ),
            )
        )

        if branch_id is None:
            assignment_query = assignment_query.where(
                RoleAssignment.branch_id.is_(None)
            )
        else:
            assignment_query = assignment_query.where(
                (
                    RoleAssignment.branch_id.is_(None)
                )
                | (
                    RoleAssignment.branch_id == branch_id
                )
            )

        result = await self.session.execute(
            assignment_query.limit(1)
        )

        return result.scalar_one_or_none() is not None