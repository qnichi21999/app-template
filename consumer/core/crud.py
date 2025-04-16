from sqlalchemy.orm import Session
from consumer.core.models import User

async def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)

async def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

async def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
