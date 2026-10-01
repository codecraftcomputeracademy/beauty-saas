import asyncio
from uuid import UUID, uuid4

from sqlalchemy import select

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.authorization.models.permission import Permission
from app.modules.authorization.models.role import Role
from app.modules.authorization.models.role_permission import RolePermission
from app.modules.authorization.services.role_management_service import (
    RoleManagementService,
)
from app.modules.authorization.services.role_permission_service import (
    RolePermissionService,
)


ORG_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")


async def create_test_role(session, code: str, name: str):
    service = RoleManagementService(session)

    return await service.create_role(
        organization_id=ORG_ID,
        code=code,
        name=name,
    )


async def get_permission(session, code: str):
    result = await session.execute(
        select(Permission).where(
            Permission.code == code,
        )
    )

    return result.scalar_one_or_none()


async def test_assign_permission():
    async with AsyncSessionLocal() as session:
        role = await create_test_role(
            session,
            "permission_assign_test",
            "Permission Assign Test",
        )

        permission = await get_permission(
            session,
            "CUSTOMER_VIEW",
        )

        if permission is None:
            raise ValueError("CUSTOMER_VIEW permission not found")

        service = RolePermissionService(session)

        role_permission = await service.assign_permission(
            role_id=role.id,
            permission_id=permission.id,
        )

        assert role_permission.role_id == role.id
        assert role_permission.permission_id == permission.id

        print("PASS: Permission assigned")

        await session.rollback()


async def test_duplicate_permission_assignment():
    async with AsyncSessionLocal() as session:
        role = await create_test_role(
            session,
            "permission_duplicate_test",
            "Permission Duplicate Test",
        )

        permission = await get_permission(
            session,
            "CUSTOMER_VIEW",
        )

        if permission is None:
            raise ValueError("CUSTOMER_VIEW permission not found")

        service = RolePermissionService(session)

        await service.assign_permission(
            role.id,
            permission.id,
        )

        try:
            await service.assign_permission(
                role.id,
                permission.id,
            )
        except ValueError as exc:
            assert str(exc) == (
                "Permission is already assigned to this role"
            )
            print("PASS: Duplicate permission assignment rejected")
        else:
            raise AssertionError(
                "Duplicate permission assignment was not rejected"
            )

        await session.rollback()


async def test_nonexistent_role():
    async with AsyncSessionLocal() as session:
        permission = await get_permission(
            session,
            "CUSTOMER_VIEW",
        )

        if permission is None:
            raise ValueError("CUSTOMER_VIEW permission not found")

        service = RolePermissionService(session)

        try:
            await service.assign_permission(
                uuid4(),
                permission.id,
            )
        except ValueError as exc:
            assert str(exc) == "Role not found"
            print("PASS: Non-existent role rejected")
        else:
            raise AssertionError(
                "Non-existent role was not rejected"
            )

        await session.rollback()


async def test_nonexistent_permission():
    async with AsyncSessionLocal() as session:
        role = await create_test_role(
            session,
            "permission_missing_test",
            "Permission Missing Test",
        )

        service = RolePermissionService(session)

        try:
            await service.assign_permission(
                role.id,
                uuid4(),
            )
        except ValueError as exc:
            assert str(exc) == "Permission not found"
            print("PASS: Non-existent permission rejected")
        else:
            raise AssertionError(
                "Non-existent permission was not rejected"
            )

        await session.rollback()


async def test_inactive_role():
    async with AsyncSessionLocal() as session:
        role = await create_test_role(
            session,
            "inactive_role_test",
            "Inactive Role Test",
        )

        role.status = "INACTIVE"
        await session.flush()

        permission = await get_permission(
            session,
            "CUSTOMER_VIEW",
        )

        if permission is None:
            raise ValueError("CUSTOMER_VIEW permission not found")

        service = RolePermissionService(session)

        try:
            await service.assign_permission(
                role.id,
                permission.id,
            )
        except ValueError as exc:
            assert str(exc) == "Role is inactive"
            print("PASS: Inactive role rejected")
        else:
            raise AssertionError(
                "Inactive role was not rejected"
            )

        await session.rollback()


async def test_inactive_permission():
    async with AsyncSessionLocal() as session:
        role = await create_test_role(
            session,
            "inactive_permission_test",
            "Inactive Permission Test",
        )

        permission = await get_permission(
            session,
            "CUSTOMER_VIEW",
        )

        if permission is None:
            raise ValueError("CUSTOMER_VIEW permission not found")

        permission.status = "INACTIVE"
        await session.flush()

        service = RolePermissionService(session)

        try:
            await service.assign_permission(
                role.id,
                permission.id,
            )
        except ValueError as exc:
            assert str(exc) == "Permission is inactive"
            print("PASS: Inactive permission rejected")
        else:
            raise AssertionError(
                "Inactive permission was not rejected"
            )

        await session.rollback()


async def test_remove_permission():
    async with AsyncSessionLocal() as session:
        role = await create_test_role(
            session,
            "permission_remove_test",
            "Permission Remove Test",
        )

        permission = await get_permission(
            session,
            "CUSTOMER_VIEW",
        )

        if permission is None:
            raise ValueError("CUSTOMER_VIEW permission not found")

        service = RolePermissionService(session)

        await service.assign_permission(
            role.id,
            permission.id,
        )

        await service.remove_permission(
            role.id,
            permission.id,
        )

        result = await session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id,
            )
        )

        assignment = result.scalar_one_or_none()

        assert assignment is None

        print("PASS: Permission removed")

        await session.rollback()


async def test_remove_unassigned_permission():
    async with AsyncSessionLocal() as session:
        role = await create_test_role(
            session,
            "permission_remove_missing_test",
            "Permission Remove Missing Test",
        )

        permission = await get_permission(
            session,
            "CUSTOMER_VIEW",
        )

        if permission is None:
            raise ValueError("CUSTOMER_VIEW permission not found")

        service = RolePermissionService(session)

        try:
            await service.remove_permission(
                role.id,
                permission.id,
            )
        except ValueError as exc:
            assert str(exc) == (
                "Permission is not assigned to this role"
            )
            print("PASS: Removing unassigned permission rejected")
        else:
            raise AssertionError(
                "Removing unassigned permission was not rejected"
            )

        await session.rollback()


async def main():
    await test_assign_permission()
    await test_duplicate_permission_assignment()
    await test_nonexistent_role()
    await test_nonexistent_permission()
    await test_inactive_role()
    await test_inactive_permission()
    await test_remove_permission()
    await test_remove_unassigned_permission()

    print("\nAll role permission tests passed.")


if __name__ == "__main__":
    asyncio.run(main())