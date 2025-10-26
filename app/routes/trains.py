from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from .. import models, schemas
from ..services.viaggiatreno import get_departures, get_train_status, normalize_status

router = APIRouter(prefix="/trains", tags=["trains"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/status/{route_id}", response_model=list[schemas.TrainStatusOut])
def get_status(route_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.TrainStatus)
        .filter(models.TrainStatus.route_id == route_id)
        .order_by(models.TrainStatus.last_update.desc())
        .limit(20)
        .all()
    )
    return rows
