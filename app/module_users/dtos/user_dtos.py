from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    document_type: str | None = None
    document_number: str | None = None
    first_name: str
    last_name: str
    phone: str | None = None
    gender: str | None = None


class UserCreateDto(UserBase):
    password: str


class UserUpdateDto(BaseModel):
    password: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    gender: str | None = None
    is_active: bool | None = None


class UserResponseDto(UserBase):
    id: int
    username: str
    is_active: bool

    class Config:
        from_attributes = True