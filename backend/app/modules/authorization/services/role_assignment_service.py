from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.authorization.models.role import Role
from app.modules.authorization.models.role_assignment import RoleAssignment
from app.modules.identity.models.user import User
from app.modules.organization.models.branch import Branch


class RoleAssignmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_role(
        self,
        organization_id: UUID,
        user_id: UUID,
        role_id: UUID,
        branch_id: UUID | None = None,
    ) -> RoleAssignment:
        # Validate user belongs to the organization.
        user_result = await self.session.execute(
            select(User).where(
                User.id == user_id,
                User.organization_id == organization_id,
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            raise ValueError("User not found in this organization")

        if user.status != "ACTIVE":
            raise ValueError("User is inactive")

        # Validate role.
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

        # System roles are platform-defined and may be assigned
        # within any organization.
        #
        # Custom roles must belong to the same organization.
        if role.organization_id is not None:
            if role.organization_id != organization_id:
                raise ValueError(
                    "Role does not belong to this organization"
                )

        # Validate branch when assignment is branch-scoped.
        if branch_id is not None:
            branch_result = await self.session.execute(
                select(Branch.id).where(
                    Branch.id == branch_id,
                    Branch.organization_id == organization_id,
                )
            )

            if branch_result.scalar_one_or_none() is None:
                raise ValueError(
                    "Branch not found in this organization"
                )

        # Prevent duplicate active assignment.
        duplicate_query = select(RoleAssignment.id).where(
            RoleAssignment.organization_id == organization_id,
            RoleAssignment.user_id == user_id,
            RoleAssignment.role_id == role_id,
            RoleAssignment.status == "ACTIVE",
        )

        if branch_id is None:
            duplicate_query = duplicate_query.where(
                RoleAssignment.branch_id.is_(None)
            )
        else:
            duplicate_query = duplicate_query.where(
                RoleAssignment.branch_id == branch_id
            )

        duplicate_result = await self.session.execute(
            duplicate_query
        )

        if duplicate_result.scalar_one_or_none() is not None:
            raise ValueError(
                "Role is already assigned to this user"
            )

        assignment = RoleAssignment(
            organization_id=organization_id,
            user_id=user_id,
            role_id=role_id,
            branch_id=branch_id,
            status="ACTIVE",
        )

        self.session.add(assignment)

        await self.session.flush()

        return assignment

    async def set_assignment_status(
        self,
        organization_id: UUID,
        assignment_id: UUID,
        status: str,
    ) -> RoleAssignment:
        status = status.strip().upper()

        if status not in {"ACTIVE", "INACTIVE"}:
            raise ValueError(
                "Invalid assignment status"
            )

        result = await self.session.execute(
            select(RoleAssignment).where(
                RoleAssignment.id == assignment_id,
                RoleAssignment.organization_id == organization_id,
            )
        )

        assignment = result.scalar_one_or_none()

        if assignment is None:
            raise ValueError(
                "Role assignment not found"
            )

        if assignment.status == status:
            return assignment

        if status == "ACTIVE":
            duplicate_query = select(
                RoleAssignment.id
            ).where(
                RoleAssignment.organization_id == organization_id,
                RoleAssignment.user_id == assignment.user_id,
                RoleAssignment.role_id == assignment.role_id,
                RoleAssignment.status == "ACTIVE",
                RoleAssignment.id != assignment.id,
            )

            if assignment.branch_id is None:
                duplicate_query = duplicate_query.where(
                    RoleAssignment.branch_id.is_(None)
                )
            else:
                duplicate_query = duplicate_query.where(
                    RoleAssignment.branch_id == assignment.branch_id
                )

            duplicate_result = await self.session.execute(
                duplicate_query
            )

            if duplicate_result.scalar_one_or_none() is not None:
                raise ValueError(
                    "An active role assignment already exists"
                )

        assignment.status = status

        await self.session.flush()

        return assignment