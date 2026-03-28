from typing import Literal

from pydantic import BaseModel


class UserResponse(BaseModel):
    email: str
    name: str | None
    picture_url: str | None
    is_allowed: bool


class GoogleAuthRequest(BaseModel):
    id_token: str


class DevLoginRequest(BaseModel):
    email: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    user: UserResponse  


class CurrentUserResponse(BaseModel):
    user: UserResponse
