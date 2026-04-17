import uuid

from sqlalchemy.orm import Session

from app.module_workshops.models import Technician


def get_available_technician(db: Session, workshop_id: uuid.UUID) -> Technician | None:
    return (
        db.query(Technician)
        .filter(
            Technician.workshop_id == workshop_id,
            Technician.is_available.is_(True),
        )
        .first()
    )
