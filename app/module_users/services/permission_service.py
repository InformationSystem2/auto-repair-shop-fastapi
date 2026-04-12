from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.module_users.dtos.permission_dtos import PermissionCreateDto, PermissionUpdateDto
from app.module_users.models.models import Permission
from app.module_users.repositories import permission_repository


def create_permission(db: Session, dto: PermissionCreateDto) -> Permission:
    if permission_repository.get_permission_by_name(db, dto.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un permiso con el nombre '{dto.name}'",
        )
    if permission_repository.get_permission_by_action(db, dto.action):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un permiso con la acción '{dto.action}'",
        )
    permission = Permission(
        name=dto.name,
        description=dto.description,
        action=dto.action,
    )
    return permission_repository.save_permission(db, permission)


def get_all_permissions(db: Session) -> list[Permission]:
    return permission_repository.get_all_permissions(db)


def get_permission_by_id(db: Session, permission_id: int) -> Permission:
    permission = permission_repository.get_permission_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado",
        )
    return permission


def update_permission(db: Session, permission_id: int, dto: PermissionUpdateDto) -> Permission:
    permission = get_permission_by_id(db, permission_id)

    if dto.name is not None:
        existing = permission_repository.get_permission_by_name(db, dto.name)
        if existing and existing.id != permission_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un permiso con el nombre '{dto.name}'",
            )
        permission.name = dto.name

    if dto.action is not None:
        existing = permission_repository.get_permission_by_action(db, dto.action)
        if existing and existing.id != permission_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un permiso con la acción '{dto.action}'",
            )
        permission.action = dto.action

    if dto.description is not None:
        permission.description = dto.description

    return permission_repository.save_permission(db, permission)


def delete_permission(db: Session, permission_id: int) -> None:
    permission = get_permission_by_id(db, permission_id)
    permission_repository.delete_permission(db, permission)
