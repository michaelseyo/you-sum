from app.schemas.auth import UserResponse


def build_user_response(user) -> UserResponse:
    return UserResponse(
        email=user.email,
        name=user.name,
        picture_url=user.picture_url,
        is_allowed=user.is_allowed,
    )
