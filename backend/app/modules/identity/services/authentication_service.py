from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.modules.identity.repositories.user_repository import UserRepository
from app.modules.identity.schemas.authentication import AuthenticationResult
from app.modules.organization.services.organization_service import (
    OrganizationService,
)


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class AuthenticationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.organization_service = OrganizationService(session)
        self.user_repository = UserRepository(session)

    async def authenticate(
        self,
        hostname: str,
        username: str,
        password: str,
    ) -> AuthenticationResult:
        organization = await self.organization_service.get_by_hostname(
            hostname
        )

        if organization is None:
            raise AuthenticationError("Authentication failed")

        if organization.status != "ACTIVE":
            raise AuthenticationError("Authentication failed")

        if organization.validity_until < date.today():
            raise AuthenticationError("Authentication failed")

        user = await self.user_repository.get_by_username(
            organization_id=organization.id,
            username=username,
        )

        if user is None:
            raise AuthenticationError("Authentication failed")

        if user.status != "ACTIVE":
            raise AuthenticationError("Authentication failed")

        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Authentication failed")

        await self.user_repository.update_last_login_at(user)

        access_token = create_access_token(user.id)

        await self.session.commit()

        return AuthenticationResult(
            access_token=access_token,
            user_id=user.id,
            organization_id=organization.id,
        )