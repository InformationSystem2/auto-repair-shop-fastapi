from sqlalchemy.orm import Session
from app.module_users.models.models import Permission


def get_all_permissions(db: Session) -> list[Permission]:
    return db.query(Permission).all()


def get_permission_by_id(db: Session, permission_id: int) -> Permission | None:
    return db.query(Permission).filter(Permission.id == permission_id).first()


def get_permission_by_name(db: Session, name: str) -> Permission | None:
    return db.query(Permission).filter(Permission.name == name).first()


def get_permission_by_action(db: Session, action: str) -> Permission | None:
    return db.query(Permission).filter(Permission.action == action).first()


def save_permission(db: Session, permission: Permission) -> Permission:
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


def delete_permission(db: Session, permission: Permission) -> None:
    db.delete(permission)
    db.commit()
