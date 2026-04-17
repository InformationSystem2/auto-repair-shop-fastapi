import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class SpecialtyBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class SpecialtyCreate(SpecialtyBase):
    pass

class SpecialtyUpdate(SpecialtyBase):
    pass

class SpecialtyResponse(SpecialtyBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
