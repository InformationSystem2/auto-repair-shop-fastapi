from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.module_users.repositories.user_repository import get_user_by_username
from app.security.config.security import create_access_token
from app.security.dto.auth_dtos import LoginRequestDto, LoginResponseDto, RoleDto

ROLE_CLIENT = "client"
ROLE_WORKSHOP_OWNER = "workshop_owner"
ROLE_TECHNICIAN = "technician"
ROLE_ADMIN = "admin"

# Páginas destino por rol (rutas del frontend Angular / Flutter deep-link)
REDIRECT_MAP = {
    ROLE_CLIENT: "/app/client/dashboard",
    ROLE_WORKSHOP_OWNER: "/app/workshop/dashboard",
    ROLE_TECHNICIAN: "/app/technician/dashboard",
    ROLE_ADMIN: "/app/admin/dashboard",
}

# Prioridad cuando un usuario tiene varios roles (el de mayor jerarquía manda)
ROLE_PRIORITY = [ROLE_ADMIN, ROLE_WORKSHOP_OWNER, ROLE_TECHNICIAN, ROLE_CLIENT]

def _resolve_redirect(role_names: set[str]) -> str:
    """Devuelve la ruta de redirección según el rol de mayor jerarquía."""
    for role in ROLE_PRIORITY:
        if role in role_names:
            return REDIRECT_MAP[role]
    return "/app/dashboard"

def login(db: Session, data: LoginRequestDto) -> LoginResponseDto:
    from app.module_users.services.user_service import verify_password

    user = get_user_by_username(db, data.username)

    if not user:
        raise  HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada. Contacta al administrador.",
        )

    if not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    role_names = {r.name for r in user.roles}

    if not role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sin roles asignados. Contacta al administrador.",
        )

    token = create_access_token(data={
        "sub": user.username,
        "user_id": str(user.id),
        "roles": list(role_names),
    })

    return LoginResponseDto(
        access_token=token,
        redirect_to=_resolve_redirect(role_names),
        user_id=str(user.id),
        user_name=user.username,
        roles=[RoleDto.model_validate(r) for r in user.roles],
    )