import asyncio
from uuid import UUID

from datetime import date
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
import app.model_registry  # noqa: F401

from app.modules.authorization.models.permission import Permission
from app.modules.authorization.models.role import Role
from app.modules.authorization.models.role_permission import RolePermission
from app.modules.authorization.models.role_assignment import RoleAssignment
from app.modules.authorization.services.authorization_service import (
    AuthorizationService,
)
from app.modules.organization.models.branch import Branch
from app.modules.organization.models.organization import Organization
from app.modules.identity.models.user import User
from app.core.security import hash_password


ORGANIZATION_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
USER_ID = UUID("30aaaffe-58ca-4bc7-9420-453c29c19992")


async def test_basic_permission_authorization():
    async with AsyncSessionLocal() as session:
        # Find an existing active permission.
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        # Create a temporary custom role.
        role = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_TEST_ROLE",
            name="Authorization Test Role",
            role_type="CUSTOM",
            status="ACTIVE",
        )
        session.add(role)
        await session.flush()

        # Give the role CUSTOMER_VIEW.
        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
        session.add(role_permission)
        await session.flush()

        # Create an org-wide assignment.
        assignment = RoleAssignment(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            role_id=role.id,
            branch_id=None,
            status="ACTIVE",
        )
        session.add(assignment)
        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | Basic permission authorization | "
            f"Expected=True, Actual={result}"
        )

        assert result is True

        await session.rollback()

async def test_unknown_permission_denied():
    async with AsyncSessionLocal() as session:
        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="DOES_NOT_EXIST",
        )

        print(
            f"PASS | Unknown permission denied | "
            f"Expected=False, Actual={result}"
        )

        assert result is False

async def test_inactive_user_denied():
    async with AsyncSessionLocal() as session:
        from app.modules.identity.models.user import User

        user_result = await session.execute(
            select(User).where(
                User.id == USER_ID,
                User.organization_id == ORGANIZATION_ID,
            )
        )
        user = user_result.scalar_one()

        original_status = user.status
        user.status = "INACTIVE"
        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | Inactive user denied | "
            f"Expected=False, Actual={result}"
        )

        assert result is False

        # Restore original state.
        user.status = original_status
        await session.flush()

        await session.rollback()

async def test_inactive_role_denied():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        role = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_INACTIVE_ROLE_TEST",
            name="Authorization Inactive Role Test",
            role_type="CUSTOM",
            status="INACTIVE",
        )
        session.add(role)
        await session.flush()

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )
        await session.flush()

        session.add(
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=None,
                status="ACTIVE",
            )
        )
        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | Inactive role denied | "
            f"Expected=False, Actual={result}"
        )

        assert result is False

        await session.rollback()

async def test_inactive_permission_denied():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
            )
        )
        permission = permission_result.scalar_one()

        original_status = permission.status
        permission.status = "INACTIVE"
        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | Inactive permission denied | "
            f"Expected=False, Actual={result}"
        )

        assert result is False

        permission.status = original_status
        await session.flush()

        await session.rollback()

async def test_wrong_organization_denied():
    async with AsyncSessionLocal() as session:
        service = AuthorizationService(session)

        wrong_organization_id = UUID(
            "11111111-1111-1111-1111-111111111111"
        )

        result = await service.has_permission(
            organization_id=wrong_organization_id,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | Wrong organization denied | "
            f"Expected=False, Actual={result}"
        )

        assert result is False

BRANCH_ID = UUID(
    "9a8d84b8-56fa-434d-8546-73ea75b35a42"
)


async def test_org_wide_role_applies_to_branch():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        role = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_ORG_WIDE_TEST",
            name="Authorization Org Wide Test",
            role_type="CUSTOM",
            status="ACTIVE",
        )
        session.add(role)
        await session.flush()

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )
        await session.flush()

        session.add(
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=None,
                status="ACTIVE",
            )
        )
        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
            branch_id=BRANCH_ID,
        )

        print(
            f"PASS | Org-wide role applies to branch | "
            f"Expected=True, Actual={result}"
        )

        assert result is True

        await session.rollback()




async def test_branch_specific_role_isolated_to_branch():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        # Create a temporary second branch.
        branch_b = Branch(
            organization_id=ORGANIZATION_ID,
            code="AUTH_TEST_BRANCH_B",
            name="Authorization Test Branch B",
            display_name="Authorization Test Branch B",
            status="ACTIVE",
            branch_type="BRANCH",
        )
        session.add(branch_b)
        await session.flush()

        # Create branch-specific role.
        role = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_BRANCH_TEST",
            name="Authorization Branch Test",
            role_type="CUSTOM",
            status="ACTIVE",
        )
        session.add(role)
        await session.flush()

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )
        await session.flush()

        # Assign role ONLY to Branch A.
        session.add(
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=BRANCH_ID,
                status="ACTIVE",
            )
        )
        await session.flush()

        service = AuthorizationService(session)

        # Branch A → should be allowed.
        branch_a_result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
            branch_id=BRANCH_ID,
        )

        print(
            f"PASS | Branch-specific role on assigned branch | "
            f"Expected=True, Actual={branch_a_result}"
        )

        assert branch_a_result is True

        # Branch B → should be denied.
        branch_b_result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
            branch_id=branch_b.id,
        )

        print(
            f"PASS | Branch-specific role blocked on other branch | "
            f"Expected=False, Actual={branch_b_result}"
        )

        assert branch_b_result is False

        await session.rollback()
async def test_branch_specific_role_not_valid_for_org_level_request():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        role = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_ORG_LEVEL_TEST",
            name="Authorization Org Level Test",
            role_type="CUSTOM",
            status="ACTIVE",
        )
        session.add(role)
        await session.flush()

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )
        await session.flush()

        # Branch-specific assignment only.
        session.add(
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=BRANCH_ID,
                status="ACTIVE",
            )
        )
        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
            branch_id=None,
        )

        print(
            f"PASS | Branch-specific role blocked at org level | "
            f"Expected=False, Actual={result}"
        )

        assert result is False

        await session.rollback()

async def test_system_role_is_tenant_scoped():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        # System role: organization_id must be NULL.
        role = Role(
            organization_id=None,
            code="AUTH_SYSTEM_TEST",
            name="Authorization System Test",
            role_type="SYSTEM",
            status="ACTIVE",
        )
        session.add(role)
        await session.flush()

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )
        await session.flush()

        # Assignment is explicitly scoped to our organization.
        session.add(
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=None,
                status="ACTIVE",
            )
        )
        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | System role within assigned organization | "
            f"Expected=True, Actual={result}"
        )

        assert result is True

        await session.rollback()
async def test_system_role_cannot_cross_organization():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        # Temporary Organization A.
        organization_a = Organization(
            client_id="AUTH-TEST-A",
            name="Authorization Test Organization A",
            legal_name="Authorization Test Organization A",
            slug="auth-test-organization-a",
            code="AUTH-TEST-A",
            email="auth-a@test.local",
            timezone="Asia/Kolkata",
            currency_code="INR",
            locale="en-IN",
            country_code="IN",
            status="ACTIVE",
            validity_until=date(2099, 12, 31),
        )
        session.add(organization_a)
        await session.flush()

        # Temporary Organization B.
        organization_b = Organization(
            client_id="AUTH-TEST-B",
            name="Authorization Test Organization B",
            legal_name="Authorization Test Organization B",
            slug="auth-test-organization-b",
            code="AUTH-TEST-B",
            email="auth-b@test.local",
            timezone="Asia/Kolkata",
            currency_code="INR",
            locale="en-IN",
            country_code="IN",
            status="ACTIVE",
            validity_until=date(2099, 12, 31),
        )
        session.add(organization_b)
        await session.flush()

        # User belongs to Organization A.
        user_a = User(
            organization_id=organization_a.id,
            username="auth_system_test_user",
            password_hash=hash_password("Test@12345"),
            email="auth-system@test.local",
            first_name="Auth",
            last_name="Test",
            display_name="Auth System Test",
            status="ACTIVE",
        )
        session.add(user_a)
        await session.flush()

        # Global system role.
        role = Role(
            organization_id=None,
            code="AUTH_CROSS_ORG_SYSTEM_TEST",
            name="Authorization Cross Org System Test",
            role_type="SYSTEM",
            status="ACTIVE",
        )
        session.add(role)
        await session.flush()

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )
        await session.flush()

        # Assignment is scoped ONLY to Organization A.
        session.add(
            RoleAssignment(
                organization_id=organization_a.id,
                user_id=user_a.id,
                role_id=role.id,
                branch_id=None,
                status="ACTIVE",
            )
        )
        await session.flush()

        service = AuthorizationService(session)

        # Organization A → allowed.
        result_a = await service.has_permission(
            organization_id=organization_a.id,
            user_id=user_a.id,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | System role in assigned organization | "
            f"Expected=True, Actual={result_a}"
        )

        assert result_a is True

        # Organization B → must be denied.
        result_b = await service.has_permission(
            organization_id=organization_b.id,
            user_id=user_a.id,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | System role blocked across organization | "
            f"Expected=False, Actual={result_b}"
        )

        assert result_b is False

        await session.rollback()

async def test_any_applicable_role_can_grant_permission():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        role_without_permission = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_ANY_ROLE_NO_PERMISSION",
            name="Authorization Any Role No Permission",
            role_type="CUSTOM",
            status="ACTIVE",
        )

        role_with_permission = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_ANY_ROLE_WITH_PERMISSION",
            name="Authorization Any Role With Permission",
            role_type="CUSTOM",
            status="ACTIVE",
        )

        session.add_all([
            role_without_permission,
            role_with_permission,
        ])
        await session.flush()

        session.add(
            RolePermission(
                role_id=role_with_permission.id,
                permission_id=permission.id,
            )
        )

        session.add_all([
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role_without_permission.id,
                branch_id=None,
                status="ACTIVE",
            ),
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role_with_permission.id,
                branch_id=None,
                status="ACTIVE",
            ),
        ])

        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | Any applicable role grants permission | "
            f"Expected=True, Actual={result}"
        )

        assert result is True

        await session.rollback()

async def test_future_role_assignment_not_yet_valid():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        role = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_FUTURE_VALIDITY_TEST",
            name="Authorization Future Validity Test",
            role_type="CUSTOM",
            status="ACTIVE",
        )
        session.add(role)
        await session.flush()

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )

        future_time = datetime.now(timezone.utc) + timedelta(days=1)

        session.add(
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=None,
                status="ACTIVE",
                valid_from=future_time,
            )
        )

        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | Future role assignment denied | "
            f"Expected=False, Actual={result}"
        )

        assert result is False

        await session.rollback()

async def test_expired_role_assignment_denied():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        role = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_EXPIRED_VALIDITY_TEST",
            name="Authorization Expired Validity Test",
            role_type="CUSTOM",
            status="ACTIVE",
        )
        session.add(role)
        await session.flush()

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )

        expired_time = datetime.now(timezone.utc) - timedelta(days=1)

        session.add(
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=None,
                status="ACTIVE",
                valid_until=expired_time,
            )
        )

        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | Expired role assignment denied | "
            f"Expected=False, Actual={result}"
        )

        assert result is False

        await session.rollback()

async def test_currently_valid_role_assignment_allowed():
    async with AsyncSessionLocal() as session:
        permission_result = await session.execute(
            select(Permission).where(
                Permission.code == "CUSTOMER_VIEW",
                Permission.status == "ACTIVE",
            )
        )
        permission = permission_result.scalar_one()

        role = Role(
            organization_id=ORGANIZATION_ID,
            code="AUTH_CURRENT_VALIDITY_TEST",
            name="Authorization Current Validity Test",
            role_type="CUSTOM",
            status="ACTIVE",
        )
        session.add(role)
        await session.flush()

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )

        now = datetime.now(timezone.utc)

        session.add(
            RoleAssignment(
                organization_id=ORGANIZATION_ID,
                user_id=USER_ID,
                role_id=role.id,
                branch_id=None,
                status="ACTIVE",
                valid_from=now - timedelta(days=1),
                valid_until=now + timedelta(days=1),
            )
        )

        await session.flush()

        service = AuthorizationService(session)

        result = await service.has_permission(
            organization_id=ORGANIZATION_ID,
            user_id=USER_ID,
            permission_code="CUSTOMER_VIEW",
        )

        print(
            f"PASS | Currently valid role assignment allowed | "
            f"Expected=True, Actual={result}"
        )

        assert result is True

        await session.rollback()

async def main():
    await test_basic_permission_authorization()
    await test_unknown_permission_denied()
    await test_inactive_user_denied()
    await test_inactive_role_denied()
    await test_inactive_permission_denied()
    await test_wrong_organization_denied()
    await test_org_wide_role_applies_to_branch()
    await test_branch_specific_role_isolated_to_branch()
    await test_branch_specific_role_not_valid_for_org_level_request()
    await test_system_role_is_tenant_scoped()
    await test_system_role_cannot_cross_organization()
    await test_any_applicable_role_can_grant_permission()
    await test_future_role_assignment_not_yet_valid()
    await test_expired_role_assignment_denied()
    await test_currently_valid_role_assignment_allowed()

asyncio.run(main())