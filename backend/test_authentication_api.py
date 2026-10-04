import asyncio

import app.model_registry  # noqa: F401

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.modules.identity.api.authentication import login
from app.modules.identity.schemas.authentication import AuthenticationResult
from app.modules.identity.schemas.login import LoginRequest


ORGANIZATION_HOSTNAME = "test-beauty.localhost"
USERNAME = "authorization_test_user"
PASSWORD = "Test@12345"


async def test_successful_login():
    async with AsyncSessionLocal() as session:
        request = LoginRequest(
            hostname=ORGANIZATION_HOSTNAME,
            username=USERNAME,
            password=PASSWORD,
        )

        result = await login(
            request=request,
            session=session,
        )

        assert isinstance(result, AuthenticationResult)
        assert result.access_token
        assert result.token_type == "bearer"
        assert result.user_id is not None
        assert result.organization_id is not None

        print("PASS: successful login")
        print("PASS: AuthenticationResult returned")


async def test_wrong_password():
    async with AsyncSessionLocal() as session:
        request = LoginRequest(
            hostname=ORGANIZATION_HOSTNAME,
            username=USERNAME,
            password="WrongPassword@123",
        )

        try:
            await login(
                request=request,
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Authentication failed"

            print("PASS: wrong password returns 401")
            print("PASS: generic authentication error")
            return

        raise AssertionError("Wrong password was accepted")


async def test_unknown_username():
    async with AsyncSessionLocal() as session:
        request = LoginRequest(
            hostname=ORGANIZATION_HOSTNAME,
            username="does_not_exist",
            password=PASSWORD,
        )

        try:
            await login(
                request=request,
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Authentication failed"

            print("PASS: unknown username returns 401")
            print("PASS: generic authentication error")
            return

        raise AssertionError("Unknown username was accepted")


async def test_unknown_hostname():
    async with AsyncSessionLocal() as session:
        request = LoginRequest(
            hostname="unknown-beauty.localhost",
            username=USERNAME,
            password=PASSWORD,
        )

        try:
            await login(
                request=request,
                session=session,
            )
        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Authentication failed"

            print("PASS: unknown hostname returns 401")
            print("PASS: generic authentication error")
            return

        raise AssertionError("Unknown hostname was accepted")


async def test_login_request_validation():
    try:
        LoginRequest(
            hostname="",
            username=USERNAME,
            password=PASSWORD,
        )
    except Exception:
        print("PASS: empty hostname rejected")
    else:
        raise AssertionError("Empty hostname was accepted")

    try:
        LoginRequest(
            hostname=ORGANIZATION_HOSTNAME,
            username="",
            password=PASSWORD,
        )
    except Exception:
        print("PASS: empty username rejected")
    else:
        raise AssertionError("Empty username was accepted")

    try:
        LoginRequest(
            hostname=ORGANIZATION_HOSTNAME,
            username=USERNAME,
            password="",
        )
    except Exception:
        print("PASS: empty password rejected")
    else:
        raise AssertionError("Empty password was accepted")


async def main():
    try:
        await test_successful_login()
        await test_wrong_password()
        await test_unknown_username()
        await test_unknown_hostname()
        await test_login_request_validation()

        print("\nAll Authentication API tests passed.")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())