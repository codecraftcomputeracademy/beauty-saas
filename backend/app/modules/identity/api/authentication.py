from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
# from app.database import AsyncSessionLocal
from app.modules.identity.schemas.authentication import AuthenticationResult
from app.modules.identity.schemas.login import LoginRequest
from app.modules.identity.services.authentication_service import (
    AuthenticationError,
    AuthenticationService,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# async def get_db_session():
#     async with AsyncSessionLocal() as session:
#         yield session


@router.post(
    "/login",
    response_model=AuthenticationResult,
    status_code=status.HTTP_200_OK,
)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthenticationResult:
    service = AuthenticationService(session)

    try:
        return await service.authenticate(
            hostname=request.hostname,
            username=request.username,
            password=request.password,
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )