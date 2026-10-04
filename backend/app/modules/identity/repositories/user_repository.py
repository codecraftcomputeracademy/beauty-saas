from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(
        self,
        organization_id: UUID,
        username: str,
    ) -> User | None:
        normalized_username = username.strip()

        if not normalized_username:
            return None

        result = await self.session.execute(
            select(User).where(
                User.organization_id == organization_id,
                User.username == normalized_username,
            )
        )

        return result.scalar_one_or_none()

    async def update_last_login_at(
        self,
        user: User,
    ) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        await self.session.flush()