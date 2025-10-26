from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime
from ..db.session import SessionLocal
from ..models import Route, Train, NotificationLog, User
from .viaggiatreno import get_departures, get_train_status, normalize_status
from .notifications import send_push

def _check_routes():
    db: Session = SessionLocal()
    try:
        routes = db.query(Route).filter(Route.active == True).all()
        for rt in routes:
            # Se è stato specificato un numero treno, monitora quello.
            if rt.train_number:
                status = get_train_status(rt.departure_code, rt.train_number)
                if not status:
                    continue
                _handle_status(db, rt, status, str(rt.train_number))
            else:
                # Altrimenti controlla le partenze e filtra per destinazione
                deps = get_departures(rt.departure_code)
                for tr in deps:
                    if (tr.get("destinazione") or "").strip().lower() != rt.arrival_name.strip().lower():
                        continue
                    train_code = str(tr.get("numeroTreno"))
                    _handle_status(db, rt, tr, train_code)
        db.commit()
    except Exception as e:
        db.rollback()
        print("[SCHEDULER] error:", e)
    finally:
        db.close()

def _handle_status(db: Session, rt: Route, data: dict, train_code: str):
    status, delay = normalize_status(data)
    # leggi ultimo record
    last: Train | None = (
        db.query(Train)
        .filter(Train.route_id == rt.id, Train.train_code == train_code)
        .order_by(Train.last_update.desc())
        .first()
    )
    changed = False
    if not last or last.last_status != status or last.delay_minutes != delay:
        changed = True
        new_row = Train(
            route_id=rt.id,
            train_code=train_code,
            last_status=status,
            delay_minutes=delay,
            last_update=datetime.utcnow(),
        )
        db.add(new_row)

    if changed:
        # decide messaggio
        if status == "Cancellato":
            event = "cancellazione"
            msg = f"Treno {train_code} cancellato sulla tratta {rt.departure_name} → {rt.arrival_name}."
        elif status == "Ritardo":
            event = "ritardo"
            msg = f"Treno {train_code} in ritardo di {delay} min ({rt.departure_name} → {rt.arrival_name})."
        else:
            event = "ripristino"
            msg = f"Treno {train_code} tornato in orario ({rt.departure_name} → {rt.arrival_name})."

        # invia notifica all'utente proprietario, se ha il token
        user = db.query(User).get(rt.user_id)
        if user and user.firebase_token:
            ok = send_push(user.firebase_token, "TrainWatcher", msg)
            if ok:
                db.add(NotificationLog(route_id=rt.id, train_code=train_code, event_type=event))

def start_scheduler(interval_minutes: int) -> BackgroundScheduler:
    sched = BackgroundScheduler()
    sched.add_job(_check_routes, "interval", minutes=interval_minutes, coalesce=True, max_instances=1)
    sched.start()
    print(f"[SCHEDULER] Avviato ogni {interval_minutes} minuti")
    return sched
