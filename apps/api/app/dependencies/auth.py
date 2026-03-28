from typing import Annotated
import logging

from app.clients.db import get_db
from app.repositories.users_repository import UsersRepository
from app.services.auth import AuthService, AuthenticationError, AuthorizationError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

users_repository = UsersRepository()
auth_service = AuthService(users_repository=users_repository)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        logger.warning("Request rejected because bearer authentication is missing")
        raise HTTPException(
            status_code=401,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return auth_service.authenticate_app_token(db, credentials.credentials)
    except AuthorizationError as exc:
        logger.warning("Bearer authentication rejected: %s", exc)
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc
    except AuthenticationError as exc:
        logger.warning("Bearer authentication failed: %s", exc)
        raise HTTPException(
            status_code=401,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
