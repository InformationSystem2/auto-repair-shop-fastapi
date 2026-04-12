from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.module_users.dtos.role_dtos import RoleCreateDto, RoleUpdateDto
from app.module_users.models.models import Role
from app.module_users.repositories import role_repository, permission_repository
from app.module_users.repositories import user_repository


# ── Helpers ──────────────────────────────────────────────────────────────────

def _resolve_permissions(db: Session, permission_ids: list[int]):
    """Devuelve los objetos Permission correspondientes; lanza 404 si alguno no existe."""
    permissions = []
    for pid in permission_ids:
        perm = permission_repository.get_permission_by_id(db, pid)
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permiso con id {pid} no encontrado",
            )
        permissions.append(perm)
    return permissions


# ── CRUD ─────────────────────────────────────────────────────────────────────

def create_role(db: Session, dto: RoleCreateDto) -> Role:
    if role_repository.exist_role_by_name(db, dto.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un rol con el nombre '{dto.name}'",
        )
    role = Role(name=dto.name, description=dto.description)

    # Asignar permisos si vienen en el request
    if dto.permission_ids:
        role.permissions = _resolve_permissions(db, dto.permission_ids)

    return role_repository.save_role(db, role)


def get_all_roles(db: Session) -> list[Role]:
    return role_repository.get_all_roles(db)


def get_role_by_id(db: Session, role_id: int) -> Role:
    role = role_repository.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado",
        )
    return role


def update_role(db: Session, role_id: int, dto: RoleUpdateDto) -> Role:
    role = get_role_by_id(db, role_id)

    if dto.name is not None:
        existing = role_repository.get_role_by_name(db, dto.name)
        if existing and existing.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un rol con el nombre '{dto.name}'",
            )
        role.name = dto.name

    if dto.description is not None:
        role.description = dto.description

    # Reemplazar permisos si vienen en el request
    if dto.permission_ids is not None:
        role.permissions = _resolve_permissions(db, dto.permission_ids)

    return role_repository.save_role(db, role)


def delete_role(db: Session, role_id: int) -> None:
    role = get_role_by_id(db, role_id)
    role_repository.delete_role(db, role)


# ── Asignación individual de permisos a rol ──────────────────────────────────

def assign_permission_to_role(db: Session, role_id: int, permission_id: int) -> Role:
    role = get_role_by_id(db, role_id)
    permission = permission_repository.get_permission_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado",
        )
    if permission in role.permissions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El permiso ya está asignado a este rol",
        )
    role.permissions.append(permission)
    return role_repository.save_role(db, role)


def remove_permission_from_role(db: Session, role_id: int, permission_id: int) -> Role:
    role = get_role_by_id(db, role_id)
    permission = permission_repository.get_permission_by_id(db, permission_id)
    if not permission or permission not in role.permissions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El permiso no está asignado a este rol",
        )
    role.permissions.remove(permission)
    return role_repository.save_role(db, role)


# ── Asignación individual de roles a usuario ─────────────────────────────────

def assign_role_to_user(db: Session, user_id: UUID, role_id: int) -> Role:
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    role = get_role_by_id(db, role_id)
    if role in user.roles:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El rol ya está asignado a este usuario",
        )
    user.roles.append(role)
    db.commit()
    db.refresh(user)
    return role


def remove_role_from_user(db: Session, user_id: UUID, role_id: int) -> None:
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    role = get_role_by_id(db, role_id)
    if role not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El rol no está asignado a este usuario",
        )
    user.roles.remove(role)
    db.commit()
