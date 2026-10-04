from datetime import date
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_context import CurrentUserContext
from app.core.security import decode_access_token
from app.database import AsyncSessionLocal
from app.modules.authorization.services.authorization_service import (
    AuthorizationService,
)
from app.modules.identity.repositories.user_repository import UserRepository
from app.modules.organization.services.organization_service import (
    OrganizationService,
)


bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    session: AsyncSession = Depends(get_db_session),
) -> CurrentUserContext:
    authentication_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise authentication_error

    if credentials.scheme.lower() != "bearer":
        raise authentication_error

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise authentication_error

    subject = payload.get("sub")

    if not subject:
        raise authentication_error

    try:
        user_id = UUID(subject)
    except (TypeError, ValueError):
        raise authentication_error

    hostname = request.url.hostname

    if not hostname:
        raise authentication_error

    organization_service = OrganizationService(session)

    organization = await organization_service.get_by_hostname(
        hostname
    )

    if organization is None:
        raise authentication_error

    if organization.status != "ACTIVE":
        raise authentication_error

    if organization.validity_until < date.today():
        raise authentication_error

    user_repository = UserRepository(session)

    user = await user_repository.get_by_id(
        organization_id=organization.id,
        user_id=user_id,
    )

    if user is None:
        raise authentication_error

    if user.status != "ACTIVE":
        raise authentication_error

    return CurrentUserContext(
        user_id=user.id,
        organization_id=organization.id,
    )


def require_permission(
    permission_code: str,
    branch_id: UUID | None = None,
):
    async def dependency(
        current_user: CurrentUserContext = Depends(
            get_current_user_context
        ),
        session: AsyncSession = Depends(get_db_session),
    ):
        authorization_service = AuthorizationService(session)

        allowed = await authorization_service.has_permission(
            organization_id=current_user.organization_id,
            user_id=current_user.user_id,
            permission_code=permission_code,
            branch_id=branch_id,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return True

    return dependency