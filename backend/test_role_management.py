import asyncio
from uuid import UUID, uuid4

from sqlalchemy import select

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.authorization.models.role import Role
from app.modules.authorization.services.role_management_service import (
    RoleManagementService,
)


ORG_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")


async def test_create_role():
    async with AsyncSessionLocal() as session:
        service = RoleManagementService(session)

        role = await service.create_role(
            organization_id=ORG_ID,
            code="salon_manager",
            name="Salon Manager",
            description="Manages salon operations",
        )

        assert role.id is not None
        assert role.code == "SALON_MANAGER"
        assert role.name == "Salon Manager"
        assert role.role_type == "CUSTOM"
        assert role.status == "ACTIVE"

        print("PASS: Create role")

        await session.rollback()


async def test_duplicate_role_code():
    async with AsyncSessionLocal() as session:
        service = RoleManagementService(session)

        await service.create_role(
            organization_id=ORG_ID,
            code="duplicate_code_test",
            name="First Role",
        )

        try:
            await service.create_role(
                organization_id=ORG_ID,
                code="DUPLICATE_CODE_TEST",
                name="Second Role",
            )
        except ValueError as exc:
            assert str(exc) == "Role code already exists in this organization"
            print("PASS: Duplicate role code rejected")
        else:
            raise AssertionError("Duplicate role code was not rejected")

        await session.rollback()


async def test_duplicate_role_name():
    async with AsyncSessionLocal() as session:
        service = RoleManagementService(session)

        await service.create_role(
            organization_id=ORG_ID,
            code="first_name_test",
            name="Duplicate Name Test",
        )

        try:
            await service.create_role(
                organization_id=ORG_ID,
                code="second_name_test",
                name="Duplicate Name Test",
            )
        except ValueError as exc:
            assert str(exc) == "Role name already exists in this organization"
            print("PASS: Duplicate role name rejected")
        else:
            raise AssertionError("Duplicate role name was not rejected")

        await session.rollback()


async def test_invalid_organization():
    async with AsyncSessionLocal() as session:
        service = RoleManagementService(session)

        invalid_org_id = uuid4()

        try:
            await service.create_role(
                organization_id=invalid_org_id,
                code="invalid_org_role",
                name="Invalid Organization Role",
            )
        except ValueError as exc:
            assert str(exc) == "Organization not found"
            print("PASS: Invalid organization rejected")
        else:
            raise AssertionError("Invalid organization was not rejected")

        await session.rollback()


async def test_blank_role_code():
    async with AsyncSessionLocal() as session:
        service = RoleManagementService(session)

        try:
            await service.create_role(
                organization_id=ORG_ID,
                code="   ",
                name="Blank Code Role",
            )
        except ValueError as exc:
            assert str(exc) == "Role code is required"
            print("PASS: Blank role code rejected")
        else:
            raise AssertionError("Blank role code was not rejected")

        await session.rollback()


async def test_blank_role_name():
    async with AsyncSessionLocal() as session:
        service = RoleManagementService(session)

        try:
            await service.create_role(
                organization_id=ORG_ID,
                code="blank_name_role",
                name="   ",
            )
        except ValueError as exc:
            assert str(exc) == "Role name is required"
            print("PASS: Blank role name rejected")
        else:
            raise AssertionError("Blank role name was not rejected")

        await session.rollback()


async def test_failed_creation_leaves_no_role():
    async with AsyncSessionLocal() as session:
        service = RoleManagementService(session)

        code = "failed_creation_test"

        try:
            await service.create_role(
                organization_id=ORG_ID,
                code=code,
                name="",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid role creation was not rejected")

        result = await session.execute(
            select(Role).where(
                Role.organization_id == ORG_ID,
                Role.code == code.upper(),
            )
        )

        role = result.scalar_one_or_none()

        assert role is None
        print("PASS: Failed creation leaves no role")

        await session.rollback()


async def main():
    await test_create_role()
    await test_duplicate_role_code()
    await test_duplicate_role_name()
    await test_invalid_organization()
    await test_blank_role_code()
    await test_blank_role_name()
    await test_failed_creation_leaves_no_role()

    print("\nAll role management validation tests passed.")


if __name__ == "__main__":
    asyncio.run(main())