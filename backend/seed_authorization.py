import asyncio
from uuid import UUID

from sqlalchemy import select

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.authorization.models.permission import Permission
from app.modules.authorization.models.role import Role
from app.modules.authorization.models.role_assignment import RoleAssignment
from app.modules.authorization.models.role_permission import RolePermission
from app.modules.identity.models.user import User


ORG_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
USER_ID = UUID("30aaaffe-58ca-4bc7-9420-453c29c19992")

ROLE_CODE = "AUTHORIZATION_TEST_ROLE"
ROLE_NAME = "Authorization Test Role"
PERMISSION_CODE = "CUSTOMER_VIEW"


async def seed_authorization():
    async with AsyncSessionLocal() as session:
        # ---------------------------------------------------------
        # 1. Verify test user
        # ---------------------------------------------------------
        result = await session.execute(
            select(User).where(
                User.id == USER_ID,
                User.organization_id == ORG_ID,
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise RuntimeError(
                "Authorization test user was not found."
            )

        print(f"USER: {user.username}")

        # ---------------------------------------------------------
        # 2. Find permission
        # ---------------------------------------------------------
        result = await session.execute(
            select(Permission).where(
                Permission.code == PERMISSION_CODE,
            )
        )
        permission = result.scalar_one_or_none()

        if permission is None:
            raise RuntimeError(
                f"Permission '{PERMISSION_CODE}' was not found. "
                "Run seed_permissions.py first."
            )

        print(f"PERMISSION: {permission.code}")

        # ---------------------------------------------------------
        # 3. Find or create organization-specific role
        # ---------------------------------------------------------
        result = await session.execute(
            select(Role).where(
                Role.organization_id == ORG_ID,
                Role.code == ROLE_CODE,
            )
        )
        role = result.scalar_one_or_none()

        if role is None:
            role = Role(
                organization_id=ORG_ID,
                code=ROLE_CODE,
                name=ROLE_NAME,
                description="Role used for authorization testing",
                role_type="CUSTOM",
                status="ACTIVE",
            )

            session.add(role)
            await session.flush()

            print(f"CREATED ROLE: {role.code}")
        else:
            print(f"EXISTS ROLE: {role.code}")

        # ---------------------------------------------------------
        # 4. Find or create role → permission mapping
        # ---------------------------------------------------------
        result = await session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id,
            )
        )
        role_permission = result.scalar_one_or_none()

        if role_permission is None:
            role_permission = RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )

            session.add(role_permission)
            await session.flush()

            print(
                f"CREATED ROLE PERMISSION: "
                f"{role.code} -> {permission.code}"
            )
        else:
            print(
                f"EXISTS ROLE PERMISSION: "
                f"{role.code} -> {permission.code}"
            )

        # ---------------------------------------------------------
        # 5. Find or create organization-wide role assignment
        # ---------------------------------------------------------
        result = await session.execute(
            select(RoleAssignment).where(
                RoleAssignment.organization_id == ORG_ID,
                RoleAssignment.user_id == USER_ID,
                RoleAssignment.role_id == role.id,
                RoleAssignment.branch_id.is_(None),
                RoleAssignment.status == "ACTIVE",
            )
        )
        assignment = result.scalar_one_or_none()

        if assignment is None:
            assignment = RoleAssignment(
                organization_id=ORG_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=None,
                status="ACTIVE",
                valid_from=None,
                valid_until=None,
            )

            session.add(assignment)
            await session.flush()

            print(
                f"CREATED ROLE ASSIGNMENT: "
                f"{user.username} -> {role.code}"
            )
        else:
            print(
                f"EXISTS ROLE ASSIGNMENT: "
                f"{user.username} -> {role.code}"
            )

        await session.commit()

        print()
        print("Authorization seed completed.")
        print(f"User:       {user.username}")
        print(f"Role:       {role.code}")
        print(f"Permission: {permission.code}")
        print("Scope:      Organization-wide")


if __name__ == "__main__":
    asyncio.run(seed_authorization())