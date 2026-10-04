from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    hostname: str = Field(min_length=1, max_length=255)
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)