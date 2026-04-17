import uuid
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status
from app.module_workshops.repositories.technician_repository import TechnicianRepository
from app.module_workshops.models.models import Technician
from app.module_workshops.dtos.technician_dto import TechnicianCreate, TechnicianUpdate
from app.module_users.repositories import user_repository
from app.module_users.models.models import Role
from app.module_users.services.user_service import get_password_hash, _generate_username

class TechnicianService:
    def __init__(self, db: Session):
        self.repository = TechnicianRepository(db)
        self.db = db

    def get_owner_workshop_id(self, owner_user_id: uuid.UUID) -> uuid.UUID:
        owner_profile = self.repository.get_by_id(owner_user_id)
        if not owner_profile:
            raise HTTPException(status_code=404, detail="Perfil de dueño de taller no encontrado")
        return owner_profile.workshop_id

    def create(self, workshop_id: uuid.UUID, dto: TechnicianCreate, created_by_id: uuid.UUID = None) -> Technician:
        if user_repository.get_user_by_email(self.db, dto.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El email '{dto.email}' ya está registrado"
            )
            
        role = self.db.query(Role).filter(Role.name == "technician").first()
        if not role:
            raise HTTPException(status_code=500, detail="Rol 'technician' no existe en el sistema.")

        technician = Technician(
            username=_generate_username(self.db),
            name=dto.name,
            last_name=dto.last_name,
            email=dto.email,
            password=get_password_hash(dto.password),
            phone=dto.phone,
            is_active=True,
            is_available=dto.is_available,
            workshop_id=workshop_id,
            created_by_id=created_by_id
        )
        technician.roles = [role]
        return self.repository.create(technician)

    def get_by_id_and_workshop(self, technician_id: uuid.UUID, workshop_id: uuid.UUID, created_by_id: uuid.UUID = None) -> Technician:
        technician = self.repository.get_by_id(technician_id)
        if not technician or technician.workshop_id != workshop_id:
            raise HTTPException(status_code=404, detail="Technician not found for this workshop")
        
        if created_by_id and technician.created_by_id != created_by_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this technician")
            
        return technician

    def get_all_by_workshop(self, workshop_id: uuid.UUID, created_by_id: uuid.UUID = None) -> List[Technician]:
        technicians = self.repository.get_by_workshop(workshop_id)
        if created_by_id:
            return [t for t in technicians if t.created_by_id == created_by_id]
        return technicians

    def update(self, workshop_id: uuid.UUID, technician_id: uuid.UUID, dto: TechnicianUpdate, created_by_id: uuid.UUID = None) -> Technician:
        technician = self.get_by_id_and_workshop(technician_id, workshop_id, created_by_id)
        if dto.name is not None:
            technician.name = dto.name
        if dto.last_name is not None:
            technician.last_name = dto.last_name
        if dto.phone is not None:
            technician.phone = dto.phone
        if dto.is_available is not None:
            technician.is_available = dto.is_available
            
        return self.repository.update(technician)

    def delete(self, workshop_id: uuid.UUID, technician_id: uuid.UUID, created_by_id: uuid.UUID = None):
        technician = self.get_by_id_and_workshop(technician_id, workshop_id, created_by_id)
        self.repository.delete(technician)
