from sqlalchemy.orm import Session
from app.module_users.models.models import Role


def get_all_roles(db: Session) -> list[Role]:
    return db.query(Role).all()

def get_role_by_id(db: Session, role_id: int) -> Role | None:
    return db.query(Role).filter(Role.id == role_id).first()

def get_role_by_name(db: Session, role_name: str) -> Role | None:
    return db.query(Role).filter(Role.name == role_name).first()

def exist_role_by_name(db: Session, role_name: str) -> bool:
    return db.query(Role).filter(Role.name == role_name).first() is not None

def save_role(db: Session, role: Role) -> Role:
    db.add(role)
    db.commit()
    db.refresh(role)
    return role