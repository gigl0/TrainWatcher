from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from .. import schemas, models
from ..services.viaggiatreno import get_station_code

router = APIRouter(prefix="/routes", tags=["routes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=list[schemas.RouteOut])
def list_routes(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Route).filter(models.Route.user_id == user_id).all()

@router.post("", response_model=schemas.RouteOut)
def create_route(payload: schemas.RouteCreate, db: Session = Depends(get_db)):
    dep_code = get_station_code(payload.departure_name)
    arr_code = get_station_code(payload.arrival_name)
    if not dep_code or not arr_code:
        raise HTTPException(status_code=400, detail="Stazione non trovata (controlla i nomi).")
    rt = models.Route(
        user_id=payload.user_id,
        departure_name=payload.departure_name,
        arrival_name=payload.arrival_name,
        departure_code=dep_code,
        arrival_code=arr_code,
        train_number=payload.train_number,
        active=payload.active,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt

@router.delete("/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db)):
    rt = db.query(models.Route).get(route_id)
    if not rt:
        raise HTTPException(404, "Route non trovata")
    db.delete(rt)
    db.commit()
    return {"deleted": route_id}
