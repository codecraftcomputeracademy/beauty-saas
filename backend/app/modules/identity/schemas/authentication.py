from uuid import UUID

from pydantic import BaseModel


class AuthenticationResult(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    organization_id: UUID