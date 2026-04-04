from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.module_users.dtos.user_dtos import UserResponseDto, UserCreateDto, UserUpdateDto
from app.module_users.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponseDto, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreateDto, db: Session = Depends(get_db)) -> UserResponseDto:
    return user_service.create_user(db, user_data)


@router.get("/", response_model=list[UserResponseDto], status_code=status.HTTP_200_OK)
def get_all_users(db: Session = Depends(get_db)) -> list[UserResponseDto]:
    return user_service.get_all_users(db)


@router.get("/{user_id}", response_model=UserResponseDto, status_code=status.HTTP_200_OK)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)) -> UserResponseDto:
    return user_service.get_user_by_id(db, user_id)


@router.put("/{user_id}", response_model=UserResponseDto, status_code=status.HTTP_200_OK)
def update_user(user_id: int, user_data: UserUpdateDto, db: Session = Depends(get_db)) -> UserResponseDto:
    return user_service.update_user(db, user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    user_service.delete_user(db, user_id)