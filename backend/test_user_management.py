
import asyncio
from uuid import UUID

from sqlalchemy import select

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401
from app.core.security import hash_password, verify_password

from app.modules.identity.models.user import User
from app.modules.identity.services.user_management_service import (
    UserManagementService,
)


ORG_ID = UUID(
    "5d3602f7-042b-4422-a030-5360569b68e5"
)

INVALID_ORG_ID = UUID(
    "00000000-0000-0000-0000-000000000001"
)


async def test_valid_user_creation(
    service: UserManagementService,
):
    username = "test.user.valid"

    user = await service.create_user(
        organization_id=ORG_ID,
        username=username,
        # password_hash="test-hashed-password",
        password="TestPassword@123",
        email="test.user.valid@example.com",
        phone="9999999999",
        first_name="Test",
        last_name="User",
        display_name="Test User",
    )

    print("Valid user creation: PASS")
    print(f"ID: {user.id}")
    print(f"Username: {user.username}")
    print(f"Organization ID: {user.organization_id}")
    print(f"Status: {user.status}")


async def test_duplicate_username(
    service: UserManagementService,
):
    username = "test.user.duplicate"

    user = await service.create_user(
        organization_id=ORG_ID,
        username=username,
        # password_hash="test-hashed-password",
        password="TestPassword@123",
        email="duplicate.test@example.com",
        first_name="Duplicate",
        last_name="Test",
        display_name="Duplicate Test",
    )

    print("\nFirst duplicate-test user created: PASS")
    print(f"ID: {user.id}")

    try:
        await service.create_user(
            organization_id=ORG_ID,
            username=username,
            # password_hash="another-test-hashed-password",
            password="TestPassword@123",
            email="another@example.com",
            first_name="Another",
            last_name="User",
            display_name="Another User",
        )

        print("Duplicate username: FAIL")
        print("ERROR: Duplicate username was allowed")

    except ValueError as exc:
        print("Duplicate username: PASS")
        print(f"Reason: {exc}")

    result = await service.session.execute(
        select(User).where(
            User.organization_id == ORG_ID,
            User.username == username,
        )
    )

    users = result.scalars().all()

    if len(users) == 1:
        print("Duplicate username count check: PASS")
        print(f"Matching users found: {len(users)}")
    else:
        print("Duplicate username count check: FAIL")
        print(f"Matching users found: {len(users)}")


async def test_invalid_organization(
    service: UserManagementService,
):
    try:
        await service.create_user(
            organization_id=INVALID_ORG_ID,
            username="test.invalid.organization",
            # password_hash="test-hashed-password",
            password="TestPassword@123",
            email="invalid.organization@example.com",
            first_name="Invalid",
            last_name="Organization",
            display_name="Invalid Organization",
        )

        print("\nInvalid organization: FAIL")
        print("ERROR: User was created for invalid organization")

    except ValueError as exc:
        print("\nInvalid organization: PASS")
        print(f"Reason: {exc}")

async def test_get_user(
    service: UserManagementService,
):
    username = "test.user.get"

    user = await service.create_user(
        organization_id=ORG_ID,
        username=username,
        # password_hash="test-hashed-password",
        password="TestPassword@123",
        email="test.user.get@example.com",
        first_name="Get",
        last_name="User",
        display_name="Get User",
    )

    found_user = await service.get_user(
        organization_id=ORG_ID,
        user_id=user.id,
    )

    if found_user is None:
        print("\nGet user: FAIL")
        print("ERROR: User was not found")
        return

    if found_user.id != user.id:
        print("\nGet user: FAIL")
        print("ERROR: Wrong user returned")
        return

    print("\nGet user: PASS")
    print(f"ID: {found_user.id}")
    print(f"Username: {found_user.username}")

async def test_get_user_wrong_organization(
    service: UserManagementService,
):
    username = "test.user.wrong.organization"

    user = await service.create_user(
        organization_id=ORG_ID,
        username=username,
        # password_hash="test-hashed-password",
        password="TestPassword@123",
        first_name="Wrong",
        last_name="Organization",
    )

    found_user = await service.get_user(
        organization_id=INVALID_ORG_ID,
        user_id=user.id,
    )

    if found_user is None:
        print("\nGet user wrong organization: PASS")
    else:
        print("\nGet user wrong organization: FAIL")
        print("ERROR: User was returned across organizations")

async def test_update_user(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.user.update",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
        email="old@example.com",
        phone="9999999999",
        first_name="Old",
        last_name="Name",
        display_name="Old Name",
    )

    updated_user = await service.update_user(
        organization_id=ORG_ID,
        user_id=user.id,
        username="test.user.updated",
        email="new@example.com",
        phone="8888888888",
        first_name="New",
        last_name="Name",
        display_name="New Name",
    )

    if updated_user is None:
        print("\nUpdate user: FAIL")
        print("ERROR: User was not found")
        return

    if (
        updated_user.username == "test.user.updated"
        and updated_user.email == "new@example.com"
        and updated_user.phone == "8888888888"
        and updated_user.first_name == "New"
        and updated_user.last_name == "Name"
        and updated_user.display_name == "New Name"
    ):
        print("\nUpdate user: PASS")
    else:
        print("\nUpdate user: FAIL")
        print("ERROR: User fields were not updated correctly")

async def test_update_user_wrong_organization(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.user.update.isolation",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
        first_name="Original",
    )

    updated_user = await service.update_user(
        organization_id=INVALID_ORG_ID,
        user_id=user.id,
        first_name="Should Not Update",
    )

    if updated_user is None:
        print("\nUpdate user wrong organization: PASS")
    else:
        print("\nUpdate user wrong organization: FAIL")
        print("ERROR: Cross-organization update was allowed")

async def test_update_user_duplicate_username(
    service: UserManagementService,
):
    first_user = await service.create_user(
        organization_id=ORG_ID,
        username="test.update.first",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
    )

    await service.create_user(
        organization_id=ORG_ID,
        username="test.update.second",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
    )

    try:
        await service.update_user(
            organization_id=ORG_ID,
            user_id=first_user.id,
            username="test.update.second",
        )

        print("\nUpdate duplicate username: FAIL")
        print("ERROR: Duplicate username was allowed")

    except ValueError as exc:
        print("\nUpdate duplicate username: PASS")
        print(f"Reason: {exc}")

async def test_set_user_status(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.user.status",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
        first_name="Status",
        last_name="Test",
    )

    deactivated_user = await service.set_user_status(
        organization_id=ORG_ID,
        user_id=user.id,
        status="INACTIVE",
    )

    if (
        deactivated_user is not None
        and deactivated_user.status == "INACTIVE"
    ):
        print("\nDeactivate user: PASS")
    else:
        print("\nDeactivate user: FAIL")

    activated_user = await service.set_user_status(
        organization_id=ORG_ID,
        user_id=user.id,
        status="ACTIVE",
    )

    if (
        activated_user is not None
        and activated_user.status == "ACTIVE"
    ):
        print("Activate user: PASS")
    else:
        print("Activate user: FAIL")

async def test_invalid_user_status(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.user.invalid.status",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
    )

    try:
        await service.set_user_status(
            organization_id=ORG_ID,
            user_id=user.id,
            status="DELETED",
        )

        print("\nInvalid user status: FAIL")
        print("ERROR: Invalid status was accepted")

    except ValueError as exc:
        print("\nInvalid user status: PASS")
        print(f"Reason: {exc}")

async def test_set_user_status_wrong_organization(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.user.status.isolation",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
    )

    updated_user = await service.set_user_status(
        organization_id=INVALID_ORG_ID,
        user_id=user.id,
        status="INACTIVE",
    )

    if updated_user is None:
        print("\nSet user status wrong organization: PASS")
    else:
        print("\nSet user status wrong organization: FAIL")
        print("ERROR: Cross-organization status change was allowed")

async def test_administrator_cannot_be_deactivated(
    service: UserManagementService,
):
    from app.modules.organization.models.organization import (
        Organization,
    )

    result = await service.session.execute(
        select(Organization.administrator_user_id).where(
            Organization.id == ORG_ID,
        )
    )

    administrator_user_id = result.scalar_one_or_none()

    if administrator_user_id is None:
        print("\nAdministrator protection: SKIPPED")
        print("Organization has no administrator_user_id")
        return

    try:
        await service.set_user_status(
            organization_id=ORG_ID,
            user_id=administrator_user_id,
            status="INACTIVE",
        )

        print("\nAdministrator protection: FAIL")
        print("ERROR: Organization administrator was deactivated")

    except ValueError as exc:
        print("\nAdministrator protection: PASS")
        print(f"Reason: {exc}")

async def test_set_organization_administrator(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.organization.admin",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
        first_name="Organization",
        last_name="Administrator",
        display_name="Organization Administrator",
    )

    administrator = await service.set_organization_administrator(
        organization_id=ORG_ID,
        administrator_user_id=user.id,
    )

    if administrator.id == user.id:
        print("\nSet organization administrator: PASS")
    else:
        print("\nSet organization administrator: FAIL")

    from app.modules.organization.models.organization import (
        Organization,
    )

    result = await service.session.execute(
        select(Organization.administrator_user_id).where(
            Organization.id == ORG_ID,
        )
    )

    administrator_user_id = result.scalar_one_or_none()

    if administrator_user_id == user.id:
        print("Administrator database assignment: PASS")
    else:
        print("Administrator database assignment: FAIL")

async def test_set_administrator_wrong_organization(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.organization.admin.isolation",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
    )

    try:
        await service.set_organization_administrator(
            organization_id=INVALID_ORG_ID,
            administrator_user_id=user.id,
        )

        print("\nSet administrator wrong organization: FAIL")
        print("ERROR: Cross-organization administrator assignment allowed")

    except ValueError as exc:
        print("\nSet administrator wrong organization: PASS")
        print(f"Reason: {exc}")

async def test_inactive_user_cannot_be_administrator(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.inactive.admin",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
    )

    await service.set_user_status(
        organization_id=ORG_ID,
        user_id=user.id,
        status="INACTIVE",
    )

    try:
        await service.set_organization_administrator(
            organization_id=ORG_ID,
            administrator_user_id=user.id,
        )

        print("\nInactive administrator protection: FAIL")
        print("ERROR: Inactive user was assigned as administrator")

    except ValueError as exc:
        print("\nInactive administrator protection: PASS")
        print(f"Reason: {exc}")

async def test_administrator_cannot_be_deactivated(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.admin.protection",
        # password_hash="test-hashed-password",
        password="TestPassword@123",
        first_name="Admin",
        last_name="Protection",
    )

    await service.set_organization_administrator(
        organization_id=ORG_ID,
        administrator_user_id=user.id,
    )

    try:
        await service.set_user_status(
            organization_id=ORG_ID,
            user_id=user.id,
            status="INACTIVE",
        )

        print("\nAdministrator protection: FAIL")
        print("ERROR: Organization administrator was deactivated")

    except ValueError as exc:
        print("\nAdministrator protection: PASS")
        print(f"Reason: {exc}")

async def test_change_password(
    service: UserManagementService,
):
    old_password = "OldPassword@123"
    new_password = "NewPassword@456"

    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.user.password",
        password=old_password,
    )

    updated_user = await service.change_password(
        organization_id=ORG_ID,
        user_id=user.id,
        current_password=old_password,
        new_password=new_password,
    )

    if updated_user is None:
        print("\nChange password: FAIL")
        print("ERROR: User was not found")
        return

    if verify_password(
        new_password,
        updated_user.password_hash,
    ):
        print("\nChange password: PASS")
    else:
        print("\nChange password: FAIL")
        print("ERROR: New password does not verify")

    if not verify_password(
        old_password,
        updated_user.password_hash,
    ):
        print("Old password invalidated: PASS")
    else:
        print("Old password invalidated: FAIL")

async def test_change_password_wrong_current_password(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.user.password.wrong",
        password="CorrectPassword@123",
    )

    try:
        await service.change_password(
            organization_id=ORG_ID,
            user_id=user.id,
            current_password="WrongPassword@123",
            new_password="NewPassword@456",
        )

        print("\nWrong current password: FAIL")
        print("ERROR: Password change was allowed")

    except ValueError as exc:
        print("\nWrong current password: PASS")
        print(f"Reason: {exc}")

async def test_change_password_same_password(
    service: UserManagementService,
):
    password = "SamePassword@123"

    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.user.password.same",
        password=password,
    )

    try:
        await service.change_password(
            organization_id=ORG_ID,
            user_id=user.id,
            current_password=password,
            new_password=password,
        )

        print("\nSame password rejection: FAIL")
        print("ERROR: Same password was accepted")

    except ValueError as exc:
        print("\nSame password rejection: PASS")
        print(f"Reason: {exc}")

async def test_change_password_wrong_organization(
    service: UserManagementService,
):
    user = await service.create_user(
        organization_id=ORG_ID,
        username="test.user.password.isolation",
        password="CorrectPassword@123",
    )

    result = await service.change_password(
        organization_id=INVALID_ORG_ID,
        user_id=user.id,
        current_password="CorrectPassword@123",
        new_password="NewPassword@456",
    )

    if result is None:
        print("\nChange password wrong organization: PASS")
    else:
        print(
            "\nChange password wrong organization: FAIL"
        )
        print(
            "ERROR: Cross-organization password change was allowed"
        )

async def main():
    async with AsyncSessionLocal() as session:
        service = UserManagementService(session)

        print("=" * 60)
        print("USER MANAGEMENT - CREATE USER TESTS")
        print("=" * 60)

        await test_valid_user_creation(service)
        await session.rollback()

        await test_duplicate_username(service)
        await session.rollback()

        await test_invalid_organization(service)
        await session.rollback()

        await test_get_user(service)
        await session.rollback()

        await test_get_user_wrong_organization(service)
        await session.rollback()

        await test_update_user(service)
        await session.rollback()

        await test_update_user_wrong_organization(service)
        await session.rollback()

        await test_update_user_duplicate_username(service)
        await session.rollback()

        await test_set_user_status(service)
        await session.rollback()

        await test_invalid_user_status(service)
        await session.rollback()

        await test_set_user_status_wrong_organization(service)
        await session.rollback()

        await test_administrator_cannot_be_deactivated(service)
        await session.rollback()

        await test_set_organization_administrator(service)
        await session.rollback()

        await test_set_administrator_wrong_organization(service)
        await session.rollback()

        await test_inactive_user_cannot_be_administrator(service)
        await session.rollback()

        await test_administrator_cannot_be_deactivated(service)
        await session.rollback()

        await test_change_password(service)
        await session.rollback()

        await test_change_password_wrong_current_password(service)
        await session.rollback()

        await test_change_password_same_password(service)
        await session.rollback()

        await test_change_password_wrong_organization(service)
        await session.rollback()

        print("\n" + "=" * 60)
        print("ALL CREATE USER TESTS COMPLETED")
        print("=" * 60)




if __name__ == "__main__":
    asyncio.run(main())
