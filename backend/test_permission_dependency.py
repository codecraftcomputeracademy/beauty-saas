import asyncio
from uuid import UUID

import app.model_registry  # noqa: F401

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select

from app.core.auth_context import CurrentUserContext
from app.core.dependencies import (
    get_current_user_context,
    get_db_session,
    require_permission,
)
from app.core.security import create_access_token
from app.database import AsyncSessionLocal, engine
from app.modules.authorization.models.permission import Permission
from app.modules.authorization.services.authorization_service import (
    AuthorizationService,
)
from app.modules.identity.models.user import User
from app.modules.organization.models.organization import Organization


ORGANIZATION_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
USER_ID = UUID("30aaaffe-58ca-4bc7-9420-453c29c19992")

HOSTNAME = "test-beauty.localhost"
PERMISSION_CODE = "CUSTOMER_VIEW"


class MockURL:
    hostname = HOSTNAME


class MockRequest:
    url = MockURL()


def bearer_credentials(token: str):
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


async def get_test_user(session):
    result = await session.execute(
        select(User).where(
            User.id == USER_ID,
            User.organization_id == ORGANIZATION_ID,
        )
    )

    user = result.scalar_one_or_none()

    assert user is not None

    return user


async def get_permission(session, permission_code):
    result = await session.execute(
        select(Permission).where(
            Permission.code == permission_code,
        )
    )

    permission = result.scalar_one_or_none()

    assert permission is not None

    return permission


async def get_current_context(session):
    token = create_access_token(USER_ID)

    return await get_current_user_context(
        request=MockRequest(),
        credentials=bearer_credentials(token),
        session=session,
    )


async def test_allowed_permission():
    async with AsyncSessionLocal() as session:
        context = await get_current_context(session)

        assert context.user_id == USER_ID
        assert context.organization_id == ORGANIZATION_ID

        permission = await get_permission(
            session,
            PERMISSION_CODE,
        )

        authorization_service = AuthorizationService(session)

        allowed = await authorization_service.has_permission(
            organization_id=context.organization_id,
            user_id=context.user_id,
            permission_code=permission.code,
        )

        assert allowed is True

        print("PASS: authenticated user has CUSTOMER_VIEW permission")


async def test_require_permission_allows_authorized_user():
    async with AsyncSessionLocal() as session:
        current_user = await get_current_context(session)

        dependency = require_permission(
            permission_code=PERMISSION_CODE,
        )

        result = await dependency(
            current_user=current_user,
            session=session,
        )

        assert result is True

        print("PASS: require_permission allows authorized user")


async def test_require_permission_denies_unauthorized_user():
    async with AsyncSessionLocal() as session:
        current_user = await get_current_context(session)

        permission_code = "INVENTORY_TRANSFER"

        authorization_service = AuthorizationService(session)

        allowed = await authorization_service.has_permission(
            organization_id=current_user.organization_id,
            user_id=current_user.user_id,
            permission_code=permission_code,
        )

        if allowed:
            print(
                "SKIP: seeded user already has "
                "INVENTORY_TRANSFER permission"
            )
            return

        dependency = require_permission(
            permission_code=permission_code,
        )

        try:
            await dependency(
                current_user=current_user,
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 403
            assert exc.detail == "Permission denied"

            print("PASS: require_permission denies unauthorized user")
            return

        raise AssertionError(
            "Unauthorized user was allowed"
        )


async def test_unauthenticated_request():
    async with AsyncSessionLocal() as session:
        try:
            await get_current_user_context(
                request=MockRequest(),
                credentials=None,
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Authentication failed"

            print("PASS: unauthenticated request returns 401")
            return

        raise AssertionError(
            "Unauthenticated request was accepted"
        )


async def test_client_cannot_supply_organization_or_user_id():
    async with AsyncSessionLocal() as session:
        current_user = await get_current_context(session)

        dependency = require_permission(
            permission_code=PERMISSION_CODE,
        )

        # The dependency accepts CurrentUserContext, not
        # client-supplied organization_id/user_id.
        assert isinstance(current_user, CurrentUserContext)

        try:
            await dependency(
                organization_id=UUID(
                    "00000000-0000-0000-0000-000000000001"
                ),
                user_id=UUID(
                    "00000000-0000-0000-0000-000000000002"
                ),
                session=session,
            )
        except TypeError:
            print(
                "PASS: client-supplied user/org IDs "
                "are not accepted by dependency"
            )
            return

        raise AssertionError(
            "require_permission accepted client-supplied identity"
        )


async def main():
    try:
        await test_allowed_permission()
        await test_require_permission_allows_authorized_user()
        await test_require_permission_denies_unauthorized_user()
        await test_unauthenticated_request()
        await test_client_cannot_supply_organization_or_user_id()

        print("\nAll permission dependency tests passed.")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())