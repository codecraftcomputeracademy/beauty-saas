import asyncio
from uuid import UUID, uuid4

from sqlalchemy import select

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.authorization.models.role import Role
from app.modules.authorization.models.role_assignment import RoleAssignment
from app.modules.authorization.services.role_assignment_service import (
    RoleAssignmentService,
)
from app.modules.authorization.services.role_management_service import (
    RoleManagementService,
)
from app.modules.identity.models.user import User


ORG_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
USER_ID = UUID("30aaaffe-58ca-4bc7-9420-453c29c19992")

BRANCH_ID = UUID("9a8d84b8-56fa-434d-8546-73ea75b35a42")


async def create_custom_role(
    session,
    code: str,
    name: str,
):
    service = RoleManagementService(session)

    return await service.create_role(
        organization_id=ORG_ID,
        code=code,
        name=name,
    )


async def test_assign_organization_role():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_org_role",
            "Assignment Organization Role",
        )

        service = RoleAssignmentService(session)

        assignment = await service.assign_role(
            organization_id=ORG_ID,
            user_id=USER_ID,
            role_id=role.id,
        )

        assert assignment.organization_id == ORG_ID
        assert assignment.user_id == USER_ID
        assert assignment.role_id == role.id
        assert assignment.branch_id is None
        assert assignment.status == "ACTIVE"

        print("PASS: Organization-wide role assignment")

        await session.rollback()


async def test_duplicate_active_assignment():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_duplicate_role",
            "Assignment Duplicate Role",
        )

        service = RoleAssignmentService(session)

        await service.assign_role(
            ORG_ID,
            USER_ID,
            role.id,
        )

        try:
            await service.assign_role(
                ORG_ID,
                USER_ID,
                role.id,
            )
        except ValueError as exc:
            assert str(exc) == "Role is already assigned to this user"
            print("PASS: Duplicate active assignment rejected")
        else:
            raise AssertionError(
                "Duplicate active assignment was not rejected"
            )

        await session.rollback()


async def test_inactive_user():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_inactive_user",
            "Assignment Inactive User",
        )

        user_result = await session.execute(
            select(User).where(
                User.id == USER_ID,
                User.organization_id == ORG_ID,
            )
        )

        user = user_result.scalar_one()
        user.status = "INACTIVE"

        await session.flush()

        service = RoleAssignmentService(session)

        try:
            await service.assign_role(
                ORG_ID,
                USER_ID,
                role.id,
            )
        except ValueError as exc:
            assert str(exc) == "User is inactive"
            print("PASS: Inactive user rejected")
        else:
            raise AssertionError(
                "Inactive user was not rejected"
            )

        await session.rollback()


async def test_inactive_role():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_inactive_role",
            "Assignment Inactive Role",
        )

        role.status = "INACTIVE"

        await session.flush()

        service = RoleAssignmentService(session)

        try:
            await service.assign_role(
                ORG_ID,
                USER_ID,
                role.id,
            )
        except ValueError as exc:
            assert str(exc) == "Role is inactive"
            print("PASS: Inactive role rejected")
        else:
            raise AssertionError(
                "Inactive role was not rejected"
            )

        await session.rollback()


async def test_nonexistent_user():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_missing_user",
            "Assignment Missing User",
        )

        service = RoleAssignmentService(session)

        try:
            await service.assign_role(
                ORG_ID,
                uuid4(),
                role.id,
            )
        except ValueError as exc:
            assert str(exc) == "User not found in this organization"
            print("PASS: Non-existent user rejected")
        else:
            raise AssertionError(
                "Non-existent user was not rejected"
            )

        await session.rollback()


async def test_nonexistent_role():
    async with AsyncSessionLocal() as session:
        service = RoleAssignmentService(session)

        try:
            await service.assign_role(
                ORG_ID,
                USER_ID,
                uuid4(),
            )
        except ValueError as exc:
            assert str(exc) == "Role not found"
            print("PASS: Non-existent role rejected")
        else:
            raise AssertionError(
                "Non-existent role was not rejected"
            )

        await session.rollback()


async def test_invalid_branch():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_invalid_branch",
            "Assignment Invalid Branch",
        )

        service = RoleAssignmentService(session)

        try:
            await service.assign_role(
                organization_id=ORG_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=uuid4(),
            )
        except ValueError as exc:
            assert str(exc) == "Branch not found in this organization"
            print("PASS: Invalid branch rejected")
        else:
            raise AssertionError(
                "Invalid branch was not rejected"
            )

        await session.rollback()


async def test_branch_scoped_assignment():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_branch_role",
            "Assignment Branch Role",
        )

        service = RoleAssignmentService(session)

        assignment = await service.assign_role(
            organization_id=ORG_ID,
            user_id=USER_ID,
            role_id=role.id,
            branch_id=BRANCH_ID,
        )

        assert assignment.organization_id == ORG_ID
        assert assignment.user_id == USER_ID
        assert assignment.role_id == role.id
        assert assignment.branch_id == BRANCH_ID
        assert assignment.status == "ACTIVE"

        print("PASS: Branch-scoped role assignment")

        await session.rollback()


async def test_system_role_assignment():
    async with AsyncSessionLocal() as session:
        system_role = Role(
            organization_id=None,
            code="SYSTEM_SUPPORT_TEST",
            name="System Support Test",
            description="Temporary system role for testing",
            role_type="SYSTEM",
            status="ACTIVE",
        )

        session.add(system_role)

        await session.flush()

        service = RoleAssignmentService(session)

        assignment = await service.assign_role(
            organization_id=ORG_ID,
            user_id=USER_ID,
            role_id=system_role.id,
        )

        assert assignment.organization_id == ORG_ID
        assert assignment.user_id == USER_ID
        assert assignment.role_id == system_role.id
        assert assignment.branch_id is None
        assert assignment.status == "ACTIVE"

        print("PASS: System role assigned within organization")
        print(
            "PASS: System role assignment retains organization scope"
        )

        await session.rollback()

async def test_deactivate_assignment():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_deactivate_test",
            "Assignment Deactivate Test",
        )

        service = RoleAssignmentService(session)

        assignment = await service.assign_role(
            ORG_ID,
            USER_ID,
            role.id,
        )

        updated = await service.set_assignment_status(
            ORG_ID,
            assignment.id,
            "INACTIVE",
        )

        assert updated.status == "INACTIVE"

        print("PASS: Assignment deactivated")

        await session.rollback()


async def test_reactivate_assignment():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_reactivate_test",
            "Assignment Reactivate Test",
        )

        service = RoleAssignmentService(session)

        assignment = await service.assign_role(
            ORG_ID,
            USER_ID,
            role.id,
        )

        await service.set_assignment_status(
            ORG_ID,
            assignment.id,
            "INACTIVE",
        )

        updated = await service.set_assignment_status(
            ORG_ID,
            assignment.id,
            "ACTIVE",
        )

        assert updated.status == "ACTIVE"

        print("PASS: Assignment reactivated")

        await session.rollback()


async def test_invalid_assignment_status():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_invalid_status",
            "Assignment Invalid Status",
        )

        service = RoleAssignmentService(session)

        assignment = await service.assign_role(
            ORG_ID,
            USER_ID,
            role.id,
        )

        try:
            await service.set_assignment_status(
                ORG_ID,
                assignment.id,
                "DELETED",
            )
        except ValueError as exc:
            assert str(exc) == "Invalid assignment status"
            print("PASS: Invalid assignment status rejected")
        else:
            raise AssertionError(
                "Invalid assignment status was not rejected"
            )

        await session.rollback()


async def test_assignment_wrong_organization():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_wrong_org",
            "Assignment Wrong Org",
        )

        service = RoleAssignmentService(session)

        assignment = await service.assign_role(
            ORG_ID,
            USER_ID,
            role.id,
        )

        wrong_org_id = uuid4()

        try:
            await service.set_assignment_status(
                wrong_org_id,
                assignment.id,
                "INACTIVE",
            )
        except ValueError as exc:
            assert str(exc) == "Role assignment not found"
            print("PASS: Wrong organization rejected")
        else:
            raise AssertionError(
                "Wrong organization was not rejected"
            )

        await session.rollback()


async def test_nonexistent_assignment():
    async with AsyncSessionLocal() as session:
        service = RoleAssignmentService(session)

        try:
            await service.set_assignment_status(
                ORG_ID,
                uuid4(),
                "INACTIVE",
            )
        except ValueError as exc:
            assert str(exc) == "Role assignment not found"
            print("PASS: Non-existent assignment rejected")
        else:
            raise AssertionError(
                "Non-existent assignment was not rejected"
            )

        await session.rollback()


async def test_same_status_is_idempotent():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_idempotent_test",
            "Assignment Idempotent Test",
        )

        service = RoleAssignmentService(session)

        assignment = await service.assign_role(
            ORG_ID,
            USER_ID,
            role.id,
        )

        updated = await service.set_assignment_status(
            ORG_ID,
            assignment.id,
            "ACTIVE",
        )

        assert updated.id == assignment.id
        assert updated.status == "ACTIVE"

        print("PASS: Same status is idempotent")

        await session.rollback()


async def test_reactivation_blocked_by_active_assignment():
    async with AsyncSessionLocal() as session:
        role = await create_custom_role(
            session,
            "assignment_reactivation_conflict",
            "Assignment Reactivation Conflict",
        )

        service = RoleAssignmentService(session)

        first_assignment = await service.assign_role(
            ORG_ID,
            USER_ID,
            role.id,
        )

        await service.set_assignment_status(
            ORG_ID,
            first_assignment.id,
            "INACTIVE",
        )

        second_assignment = await service.assign_role(
            ORG_ID,
            USER_ID,
            role.id,
        )

        assert second_assignment.status == "ACTIVE"

        try:
            await service.set_assignment_status(
                ORG_ID,
                first_assignment.id,
                "ACTIVE",
            )
        except ValueError as exc:
            assert str(exc) == (
                "An active role assignment already exists"
            )
            print(
                "PASS: Reactivation blocked by active assignment"
            )
        else:
            raise AssertionError(
                "Reactivation conflict was not rejected"
            )

        await session.rollback()

async def main():
    await test_assign_organization_role()
    await test_duplicate_active_assignment()
    await test_inactive_user()
    await test_inactive_role()
    await test_nonexistent_user()
    await test_nonexistent_role()
    await test_invalid_branch()
    await test_branch_scoped_assignment()
    await test_system_role_assignment()

    await test_deactivate_assignment()
    await test_reactivate_assignment()
    await test_invalid_assignment_status()
    await test_assignment_wrong_organization()
    await test_nonexistent_assignment()
    await test_same_status_is_idempotent()
    await test_reactivation_blocked_by_active_assignment()

    print("\nAll role assignment tests passed.")


if __name__ == "__main__":
    asyncio.run(main())