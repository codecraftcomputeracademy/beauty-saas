from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.identity.models.user import User

from app.core.security import hash_password, verify_password

class UserManagementService:
    def __init__(self, session: AsyncSession):
        self.session = session

        
    async def create_user(
        self,
        organization_id: UUID,
        username: str,
        password: str,
        email: str | None = None,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        display_name: str | None = None,
    ) -> User:
        username = username.strip()

        if not username:
            raise ValueError("Username is required")

        if not password:
            raise ValueError("Password is required")

        # Verify that the organization exists.
        from app.modules.organization.models.organization import (
            Organization,
        )

        organization_result = await self.session.execute(
            select(Organization.id).where(
                Organization.id == organization_id,
            )
        )

        if organization_result.scalar_one_or_none() is None:
            raise ValueError("Organization not found")

        # Usernames are unique within an organization.
        existing_user_result = await self.session.execute(
            select(User.id).where(
                User.organization_id == organization_id,
                User.username == username,
            )
        )

        if existing_user_result.scalar_one_or_none() is not None:
            raise ValueError(
                "Username already exists in this organization"
            )

        user = User(
            organization_id=organization_id,
            username=username,
            password_hash=hash_password(password),
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            status="ACTIVE",
        )

        self.session.add(user)

        await self.session.flush()

        return user

    async def get_user(
            self,
            organization_id: UUID,
            user_id: UUID,             ) -> User | None:
                result = await self.session.execute(
                select(User).where(
                    User.id == user_id,
                    User.organization_id == organization_id,
                    )
                )
    
                return result.scalar_one_or_none()

    async def update_user(
        self,
        organization_id: UUID,
        user_id: UUID,
        username: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        display_name: str | None = None,
    ) -> User | None:
        user = await self.get_user(
            organization_id=organization_id,
            user_id=user_id,
        )

        if user is None:
            return None

        if username is not None:
            username = username.strip()

            if not username:
                raise ValueError("Username is required")

            existing_user_result = await self.session.execute(
                select(User.id).where(
                    User.organization_id == organization_id,
                    User.username == username,
                    User.id != user_id,
                )
            )

            if existing_user_result.scalar_one_or_none() is not None:
                raise ValueError(
                    "Username already exists in this organization"
                )

            user.username = username

        if email is not None:
            user.email = email

        if phone is not None:
            user.phone = phone

        if first_name is not None:
            user.first_name = first_name

        if last_name is not None:
            user.last_name = last_name

        if display_name is not None:
            user.display_name = display_name

        await self.session.flush()

        return user    

    async def set_user_status(
        self,
        organization_id: UUID,
        user_id: UUID,
        status: str,
    ) -> User | None:
        allowed_statuses = {
            "ACTIVE",
            "INACTIVE",
        }

        status = status.upper().strip()

        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid user status: {status}"
            )

        user = await self.get_user(
            organization_id=organization_id,
            user_id=user_id,
        )

        if user is None:
            return None

        # The organization administrator cannot be deactivated.
        from app.modules.organization.models.organization import (
            Organization,
        )

        organization_result = await self.session.execute(
            select(Organization.administrator_user_id).where(
                Organization.id == organization_id,
            )
        )

        administrator_user_id = (
            organization_result.scalar_one_or_none()
        )

        if (
            administrator_user_id == user.id
            and status == "INACTIVE"
        ):
            raise ValueError(
                "Organization administrator cannot be deactivated"
            )

        user.status = status

        await self.session.flush()

        return user

    async def set_organization_administrator(
        self,
        organization_id: UUID,
        administrator_user_id: UUID,
    ) -> User:
        from app.modules.organization.models.organization import (
            Organization,
        )

        # Verify the organization exists.
        organization_result = await self.session.execute(
            select(Organization).where(
                Organization.id == organization_id,
            )
        )

        organization = organization_result.scalar_one_or_none()

        if organization is None:
            raise ValueError("Organization not found")

        # Verify that the user belongs to this organization.
        user = await self.get_user(
            organization_id=organization_id,
            user_id=administrator_user_id,
        )

        if user is None:
            raise ValueError(
                "Administrator user does not belong to this organization"
            )

        # Administrator must be active.
        if user.status != "ACTIVE":
            raise ValueError(
                "Inactive user cannot be organization administrator"
            )

        organization.administrator_user_id = user.id

        await self.session.flush()

        return user

    async def change_password(
        self,
        organization_id: UUID,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> User | None:
        user = await self.get_user(
            organization_id=organization_id,
            user_id=user_id,
        )

        if user is None:
            return None

        if not current_password:
            raise ValueError("Current password is required")

        if not new_password:
            raise ValueError("New password is required")

        if current_password == new_password:
            raise ValueError(
                "New password must be different from current password"
            )

        if not verify_password(
            current_password,
            user.password_hash,
        ):
            raise ValueError("Current password is incorrect")

        user.password_hash = hash_password(new_password)

        await self.session.flush()

        return user

    async def mark_email_verified(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> User | None:
        user = await self.get_user(
            organization_id=organization_id,
            user_id=user_id,
        )

        if user is None:
            return None

        if user.email is None:
            raise ValueError(
                "Cannot verify email because user has no email address"
            )

        if user.email_verified_at is None:
            from datetime import datetime, timezone

            user.email_verified_at = datetime.now(timezone.utc)

            await self.session.flush()

        return user

    async def mark_phone_verified(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> User | None:
        user = await self.get_user(
            organization_id=organization_id,
            user_id=user_id,
        )

        if user is None:
            return None

        if user.phone is None:
            raise ValueError(
                "Cannot verify phone because user has no phone number"
            )

        if user.phone_verified_at is None:
            from datetime import datetime, timezone

            user.phone_verified_at = datetime.now(timezone.utc)

            await self.session.flush()

        return user

    