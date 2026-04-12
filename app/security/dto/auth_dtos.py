from pydantic import BaseModel


class LoginRequestDto(BaseModel):
    username: str
    password: str

class RoleDto(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class LoginResponseDto(BaseModel):
    access_token: str
    token_type: str = "bearer"
    redirect_to: str
    user_id: str
    user_name: str
    roles: list[RoleDto]