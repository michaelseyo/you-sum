from datetime import datetime, timezone

from app.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import Session


class UsersRepository:
    def get_by_id(self, db: Session, *, user_id: int) -> User | None:
        return db.get(User, user_id)

    def get_by_google_sub(self, db: Session, *, google_sub: str) -> User | None:
        statement = select(User).where(User.google_sub == google_sub)
        return db.scalar(statement)

    def sync_google_user(
        self,
        db: Session,
        *,
        google_sub: str,
        email: str,
        name: str | None,
        picture_url: str | None,
        is_allowed: bool,
    ) -> User:
        user = self.get_by_google_sub(db, google_sub=google_sub)
        if user is None:
            user = User(
                google_sub=google_sub,
                email=email,
                name=name,
                picture_url=picture_url,
                is_allowed=is_allowed,
            )
            db.add(user)
        else:
            user.email = email
            user.name = name
            user.picture_url = picture_url
            user.is_allowed = is_allowed

        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user
