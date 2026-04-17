import uuid
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.module_workshops.repositories.specialty_repository import SpecialtyRepository
from app.module_workshops.models.models import Specialty
from app.module_workshops.dtos.specialty_dto import SpecialtyCreate, SpecialtyUpdate

class SpecialtyService:
    def __init__(self, db: Session):
        self.repository = SpecialtyRepository(db)
        self.db = db

    def create(self, dto: SpecialtyCreate) -> Specialty:
        specialty = Specialty(name=dto.name, description=dto.description)
        return self.repository.create(specialty)

    def get_all(self) -> List[Specialty]:
        return self.repository.get_all()

    def get_by_id(self, specialty_id: uuid.UUID) -> Specialty:
        specialty = self.repository.get_by_id(specialty_id)
        if not specialty:
            raise HTTPException(status_code=404, detail="Specialty not found")
        return specialty

    def update(self, specialty_id: uuid.UUID, dto: SpecialtyUpdate) -> Specialty:
        specialty = self.get_by_id(specialty_id)
        specialty.name = dto.name
        specialty.description = dto.description
        return self.repository.update(specialty)

    def delete(self, specialty_id: uuid.UUID):
        specialty = self.get_by_id(specialty_id)
        self.repository.delete(specialty)
