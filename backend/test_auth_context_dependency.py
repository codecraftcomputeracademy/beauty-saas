import asyncio
from datetime import date, timedelta
from uuid import UUID

import app.model_registry  # noqa: F401
import jwt

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select

from app.core.auth_context import CurrentUserContext
from app.core.config import settings
from app.core.dependencies import get_current_user_context
from app.core.security import JWT_ALGORITHM, create_access_token
from app.database import AsyncSessionLocal, engine
from app.modules.identity.models.user import User
from app.modules.organization.models.organization import Organization

ORGANIZATION_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")
USER_ID = UUID("30aaaffe-58ca-4bc7-9420-453c29c19992")

HOSTNAME = "test-beauty.localhost"
USERNAME = "authorization_test_user"
PASSWORD = "Test@12345"


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


async def test_valid_token_returns_current_user_context():
    async with AsyncSessionLocal() as session:
        token = create_access_token(USER_ID)

        context = await get_current_user_context(
            request=MockRequest(),
            credentials=bearer_credentials(token),
            session=session,
        )

        assert isinstance(context, CurrentUserContext)
        assert context.user_id == USER_ID
        assert context.organization_id == ORGANIZATION_ID

        print("PASS: valid token returns CurrentUserContext")
        print("PASS: user_id comes from JWT")
        print("PASS: organization_id comes from hostname")


async def test_missing_token():
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

            print("PASS: missing token returns 401")
            return

        raise AssertionError("Missing token was accepted")


async def test_invalid_token():
    async with AsyncSessionLocal() as session:
        try:
            await get_current_user_context(
                request=MockRequest(),
                credentials=bearer_credentials(
                    "this-is-not-a-valid-jwt"
                ),
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Authentication failed"

            print("PASS: invalid token returns 401")
            return

        raise AssertionError("Invalid token was accepted")


async def test_malformed_user_id_in_token():
    async with AsyncSessionLocal() as session:
        token = jwt.encode(
            {
                "sub": "not-a-valid-uuid",
            },
            settings.jwt_secret_key,
            algorithm=JWT_ALGORITHM,
        )

        try:
            await get_current_user_context(
                request=MockRequest(),
                credentials=bearer_credentials(token),
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Authentication failed"

            print("PASS: malformed user ID returns 401")
            return

        raise AssertionError("Malformed user ID was accepted")


async def test_unknown_user():
    async with AsyncSessionLocal() as session:
        unknown_user_id = UUID(
            "00000000-0000-0000-0000-000000000001"
        )

        token = create_access_token(unknown_user_id)

        try:
            await get_current_user_context(
                request=MockRequest(),
                credentials=bearer_credentials(token),
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Authentication failed"

            print("PASS: unknown user returns 401")
            return

        raise AssertionError("Unknown user was accepted")


async def test_wrong_hostname():
    async with AsyncSessionLocal() as session:
        token = create_access_token(USER_ID)

        request = type(
            "MockRequest",
            (),
            {
                "url": type(
                    "MockURL",
                    (),
                    {"hostname": "unknown-beauty.localhost"},
                )()
            },
        )()

        try:
            await get_current_user_context(
                request=request,
                credentials=bearer_credentials(token),
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Authentication failed"

            print("PASS: unknown hostname returns 401")
            return

        raise AssertionError("Unknown hostname was accepted")


async def test_user_from_wrong_organization():
    async with AsyncSessionLocal() as session:
        user = await get_test_user(session)

        token = create_access_token(user.id)

        request = type(
            "MockRequest",
            (),
            {
                "url": type(
                    "MockURL",
                    (),
                    {"hostname": "unknown-beauty.localhost"},
                )()
            },
        )()

        try:
            await get_current_user_context(
                request=request,
                credentials=bearer_credentials(token),
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Authentication failed"

            print("PASS: user cannot authenticate against another organization")
            return

        raise AssertionError(
            "User was accepted against another organization"
        )


async def test_inactive_user():
    async with AsyncSessionLocal() as session:
        user = await get_test_user(session)

        original_status = user.status

        try:
            user.status = "INACTIVE"
            await session.commit()

            token = create_access_token(user.id)

            try:
                await get_current_user_context(
                    request=MockRequest(),
                    credentials=bearer_credentials(token),
                    session=session,
                )
            except HTTPException as exc:
                assert exc.status_code == 401
                assert exc.detail == "Authentication failed"

                print("PASS: inactive user returns 401")
                return

            raise AssertionError("Inactive user was accepted")

        finally:
            user.status = original_status
            await session.commit()


async def test_inactive_organization():
    async with AsyncSessionLocal() as session:
        organization = await session.get(
            Organization,
            ORGANIZATION_ID,
        )

        assert organization is not None

        original_status = organization.status

        try:
            organization.status = "INACTIVE"
            await session.commit()

            token = create_access_token(USER_ID)

            try:
                await get_current_user_context(
                    request=MockRequest(),
                    credentials=bearer_credentials(token),
                    session=session,
                )
            except HTTPException as exc:
                assert exc.status_code == 401
                assert exc.detail == "Authentication failed"

                print("PASS: inactive organization returns 401")
                return

            raise AssertionError(
                "Inactive organization was accepted"
            )

        finally:
            organization.status = original_status
            await session.commit()


async def test_expired_organization():
    async with AsyncSessionLocal() as session:
        organization = await session.get(
            Organization,
            ORGANIZATION_ID,
        )

        assert organization is not None

        original_validity_until = organization.validity_until
        original_status = organization.status

        try:
            organization.status = "ACTIVE"
            organization.validity_until = date.today() - timedelta(days=1)
            await session.commit()

            token = create_access_token(USER_ID)

            try:
                await get_current_user_context(
                    request=MockRequest(),
                    credentials=bearer_credentials(token),
                    session=session,
                )
            except HTTPException as exc:
                assert exc.status_code == 401
                assert exc.detail == "Authentication failed"

                print("PASS: expired organization returns 401")
                return

            raise AssertionError(
                "Expired organization was accepted"
            )

        finally:
            organization.status = original_status
            organization.validity_until = original_validity_until
            await session.commit()


async def main():
    try:
        await test_valid_token_returns_current_user_context()
        await test_missing_token()
        await test_invalid_token()
        await test_malformed_user_id_in_token()
        await test_unknown_user()
        await test_wrong_hostname()
        await test_user_from_wrong_organization()
        await test_inactive_user()
        await test_inactive_organization()
        await test_expired_organization()

        print("\nAll authentication context dependency tests passed.")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())