from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from ..models import Station

router = APIRouter(prefix="/stations", tags=["stations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def list_stations(db: Session = Depends(get_db)):
    """
    Restituisce la lista delle stazioni memorizzate in cache locale.
    """
    stations = db.query(Station).order_by(Station.name.asc()).all()
    if not stations:
        raise HTTPException(status_code=404, detail="No cached stations found")
    return [
        {"id": s.id, "name": s.name, "code": s.code}
        for s in stations
    ]


@router.delete("/")
def clear_stations_cache(db: Session = Depends(get_db)):
    """
    Svuota completamente la cache locale delle stazioni.
    Utile per forzare un nuovo recupero dei codici da Viaggiatreno.
    """
    deleted = db.query(Station).delete()
    db.commit()
    return {"message": "Cache cleared", "deleted": deleted}
