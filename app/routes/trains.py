from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from .. import models, schemas
from ..models import Route, Train
from ..services.viaggiatreno import (
    get_trains_for_route,
    get_or_cache_station_code,
)

router = APIRouter(prefix="/trains", tags=["trains"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Endpoint: stato treni formattato
@router.get("/status")
def get_trains_status(
    from_station: str = Query(..., alias="from"),
    to_station: str = Query(..., alias="to"),
    db: Session = Depends(get_db)
):
    """
    Restituisce lo stato formattato dei treni per una tratta specifica.
    """
    route = (
        db.query(Route)
        .filter(Route.departure_name.ilike(from_station))
        .filter(Route.arrival_name.ilike(to_station))
        .first()
    )

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    trains = (
        db.query(Train)
        .filter(Train.route_id == route.id)
        .order_by(Train.last_update.desc())
        .all()
    )

    if not trains:
        raise HTTPException(status_code=404, detail="No train data for this route")

    response = {
        "route": f"{route.departure_name} → {route.arrival_name}",
        "last_update": max(t.last_update for t in trains),
        "trains": [
            {
                "code": t.train_code,
                "status": t.last_status,
                "delay_minutes": t.delay_minutes
            }
            for t in trains
        ]
    }

    return response


# ✅ Endpoint: aggiornamento manuale
@router.get("/check")
def manual_check(
    from_station: str = Query(..., alias="from"),
    to_station: str = Query(..., alias="to"),
    db: Session = Depends(get_db)
):
    """
    Forza un aggiornamento immediato per la tratta specificata.
    Esempio: /trains/check?from=Pinerolo&to=Torino Porta Susa
    """
    route = (
        db.query(Route)
        .filter(Route.departure_name.ilike(from_station))
        .filter(Route.arrival_name.ilike(to_station))
        .first()
    )

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # 🔹 Se la tratta non ha ancora codici, li risolviamo ora e li cacheiamo
    if not route.departure_code or not route.arrival_code:
        route.departure_code = get_or_cache_station_code(route.departure_name, db)
        route.arrival_code = get_or_cache_station_code(route.arrival_name, db)
        db.commit()

    # 🔹 Interroga Viaggiatreno
    trains_data = get_trains_for_route(route.departure_code, route.arrival_code)

    if not trains_data:
        raise HTTPException(status_code=404, detail="No train data found for this route")

    # 🔹 Aggiorna/Inserisce nel DB
    from datetime import datetime
    for train in trains_data:
        record = Train(
            route_id=route.id,
            train_code=train["train_code"],
            last_status=train["status"],
            delay_minutes=train["delay"],
            last_update=datetime.utcnow(),
        )
        db.add(record)

    db.commit()
    return {"message": "Route refreshed successfully", "count": len(trains_data)}
