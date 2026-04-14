from typing import Literal

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    email: EmailStr
    name: str | None
    picture_url: str | None
    is_allowed: bool


class GoogleAuthRequest(BaseModel):
    id_token: str


class DevLoginRequest(BaseModel):
    email: EmailStr | None = None


class AuthResponse(BaseModel):
    access_token: str
    expires_at: int
    token_type: Literal["bearer"]
    user: UserResponse


class CurrentUserResponse(BaseModel):
    user: UserResponse
