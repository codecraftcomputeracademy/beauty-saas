import asyncio
from datetime import datetime, timezone
from uuid import UUID

import app.model_registry  # noqa: F401
import jwt

from app.core.config import settings
from app.core.security import JWT_ALGORITHM
from app.database import AsyncSessionLocal, engine
from app.modules.identity.models.user import User
from app.modules.identity.services.authentication_service import (
    AuthenticationError,
    AuthenticationService,
)
from app.modules.organization.models.organization import Organization


ORGANIZATION_HOSTNAME = "test-beauty.localhost"
USERNAME = "authorization_test_user"
PASSWORD = "Test@12345"

ORGANIZATION_ID = UUID("5d3602f7-042b-4422-a030-5360569b68e5")


async def test_successful_authentication():
    async with AsyncSessionLocal() as session:
        organization = await session.get(
            Organization,
            ORGANIZATION_ID,
        )

        assert organization is not None

        user_result = await session.execute(
            __import__("sqlalchemy").select(User).where(
                User.organization_id == organization.id,
                User.username == USERNAME,
            )
        )
        user = user_result.scalar_one_or_none()

        assert user is not None

        previous_last_login_at = user.last_login_at

        service = AuthenticationService(session)

        result = await service.authenticate(
            hostname=ORGANIZATION_HOSTNAME,
            username=USERNAME,
            password=PASSWORD,
        )

        assert result.access_token
        assert result.token_type == "bearer"
        assert result.user_id == user.id
        assert result.organization_id == organization.id

        await session.refresh(user)

        assert user.last_login_at is not None

        if previous_last_login_at is not None:
            assert user.last_login_at >= previous_last_login_at

        print("PASS: successful authentication")
        print("PASS: AuthenticationResult contains correct identity")
        print("PASS: last_login_at updated")


async def test_jwt_payload():
    async with AsyncSessionLocal() as session:
        service = AuthenticationService(session)

        result = await service.authenticate(
            hostname=ORGANIZATION_HOSTNAME,
            username=USERNAME,
            password=PASSWORD,
        )

        payload = jwt.decode(
            result.access_token,
            settings.jwt_secret_key,
            algorithms=[JWT_ALGORITHM],
        )

        assert payload["sub"] == str(result.user_id)
        assert "iat" in payload
        assert "exp" in payload
        assert "jti" in payload

        assert "organization_id" not in payload
        assert "roles" not in payload
        assert "permissions" not in payload
        assert "branch_id" not in payload
        assert "employee_id" not in payload

        print("PASS: JWT contains required claims")
        print("PASS: JWT does not contain authorization/tenant claims")


async def test_wrong_password():
    async with AsyncSessionLocal() as session:
        service = AuthenticationService(session)

        try:
            await service.authenticate(
                hostname=ORGANIZATION_HOSTNAME,
                username=USERNAME,
                password="WrongPassword@123",
            )
        except AuthenticationError as exc:
            assert str(exc) == "Authentication failed"
            print("PASS: wrong password rejected")
            print("PASS: generic authentication error")
            return

        raise AssertionError("Wrong password was accepted")


async def test_unknown_username():
    async with AsyncSessionLocal() as session:
        service = AuthenticationService(session)

        try:
            await service.authenticate(
                hostname=ORGANIZATION_HOSTNAME,
                username="does_not_exist",
                password=PASSWORD,
            )
        except AuthenticationError as exc:
            assert str(exc) == "Authentication failed"
            print("PASS: unknown username rejected")
            print("PASS: generic authentication error")
            return

        raise AssertionError("Unknown username was accepted")


async def test_unknown_hostname():
    async with AsyncSessionLocal() as session:
        service = AuthenticationService(session)

        try:
            await service.authenticate(
                hostname="unknown-beauty.localhost",
                username=USERNAME,
                password=PASSWORD,
            )
        except AuthenticationError as exc:
            assert str(exc) == "Authentication failed"
            print("PASS: unknown hostname rejected")
            print("PASS: generic authentication error")
            return

        raise AssertionError("Unknown hostname was accepted")


async def test_empty_username():
    async with AsyncSessionLocal() as session:
        service = AuthenticationService(session)

        try:
            await service.authenticate(
                hostname=ORGANIZATION_HOSTNAME,
                username="",
                password=PASSWORD,
            )
        except AuthenticationError as exc:
            assert str(exc) == "Authentication failed"
            print("PASS: empty username rejected")
            return

        raise AssertionError("Empty username was accepted")


async def test_empty_password():
    async with AsyncSessionLocal() as session:
        service = AuthenticationService(session)

        try:
            await service.authenticate(
                hostname=ORGANIZATION_HOSTNAME,
                username=USERNAME,
                password="",
            )
        except AuthenticationError as exc:
            assert str(exc) == "Authentication failed"
            print("PASS: empty password rejected")
            return

        raise AssertionError("Empty password was accepted")


async def main():
    try:
        await test_successful_authentication()
        await test_jwt_payload()
        await test_wrong_password()
        await test_unknown_username()
        await test_unknown_hostname()
        await test_empty_username()
        await test_empty_password()

        print("\nAll AuthenticationService tests passed.")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())