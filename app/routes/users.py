from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from .. import schemas, models

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=schemas.UserOut)
def register_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        # aggiorna token se cambia
        existing.firebase_token = payload.firebase_token or existing.firebase_token
        db.commit()
        db.refresh(existing)
        return existing
    u = models.User(email=payload.email, firebase_token=payload.firebase_token)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
