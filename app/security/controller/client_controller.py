from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.dto.client_dtos import ClientCreateDTO, ClientResponseDTO, ClientUpdateDTO
from app.security.service import client_service
from app.security.config.security import require_role

router = APIRouter(prefix="/api/clients", tags=["Clients"])

_allowed = Depends(require_role("admin"))


@router.get("/me", response_model=ClientResponseDTO, status_code=status.HTTP_200_OK)
def get_my_client_profile(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Devuelve el perfil de cliente del usuario autenticado (rol client requerido)."""
    return client_service.get_client_by_id(db, current_user.id)


@router.post("/", response_model=ClientResponseDTO, status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreateDTO, db: Session = Depends(get_db)):
    """Crea un usuario con rol 'client' + su perfil de cliente. Endpoint público (registro)."""
    return client_service.create_client(db, data)


@router.get("/", response_model=list[ClientResponseDTO], status_code=status.HTTP_200_OK, dependencies=[_allowed])
def get_all_clients(db: Session = Depends(get_db)):
    return client_service.get_all_clients(db)


@router.get("/{client_id}", response_model=ClientResponseDTO, status_code=status.HTTP_200_OK, dependencies=[_allowed])
def get_client(client_id: UUID, db: Session = Depends(get_db)):
    return client_service.get_client_by_id(db, client_id)


@router.put("/{client_id}", response_model=ClientResponseDTO, status_code=status.HTTP_200_OK, dependencies=[_allowed])
def update_client(client_id: UUID, data: ClientUpdateDTO, db: Session = Depends(get_db)):
    return client_service.update_client(db, client_id, data)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_allowed])
def delete_client(client_id: UUID, db: Session = Depends(get_db)):
    client_service.delete_client(db, client_id)
