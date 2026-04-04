import random

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.module_users.dtos.user_dtos import UserCreateDto, UserUpdateDto
from app.module_users.models.models import User
from app.module_users.repositories import user_repository
from app.security.config.security import get_password_hash


def create_user(db: Session, dto: UserCreateDto) -> User:
    if user_repository.get_user_by_email(db, dto.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        username=generate_username_number(db, dto),
        email=dto.email,
        document_type=dto.document_type,
        document_number=dto.document_number,
        first_name=dto.first_name,
        last_name=dto.last_name,
        phone=dto.phone,
        gender=dto.gender,
        password=get_password_hash(dto.password),
    )
    return user_repository.save_user(db, new_user)


def get_all_users(db: Session) -> list[User]:
    return user_repository.get_all_users(db)


def get_user_by_id(db: Session, user_id: int) -> User:
    user = user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_user_by_username(db: Session, username: str) -> User:
    user = user_repository.get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_user(db: Session, user_id: int, dto: UserUpdateDto) -> User:
    user = get_user_by_id(db, user_id)

    if dto.document_type is not None:
        user.document_type = dto.document_type
    if dto.document_number is not None:
        user.document_number = dto.document_number
    if dto.first_name is not None:
        user.first_name = dto.first_name
    if dto.last_name is not None:
        user.last_name = dto.last_name
    if dto.phone is not None:
        user.phone = dto.phone
    if dto.gender is not None:
        user.gender = dto.gender
    if dto.password is not None:
        user.password = get_password_hash(dto.password)
    if dto.is_active is not None:
        user.is_active = dto.is_active

    return user_repository.save_user(db, user)


def delete_user(db: Session, user_id: int) -> None:
    user = get_user_by_id(db, user_id)
    user.is_active = False
    user_repository.save_user(db, user)

def generate_username_number(db: Session, dto: UserCreateDto) -> str:
    prefix = "usr"

    while True:
        random_number = str(random.randint(100000, 999999))
        generate_username = f"{prefix}-{random_number}"

        if not user_repository.exists_user_by_username(db, generate_username):
            break

    return generate_username