# app/services/notifications.py

import datetime
from firebase_admin import messaging
from sqlalchemy.orm import Session
from app.models import NotificationLog

def send_push_notification(user_token: str, title: str, body: str) -> bool:
    """Invia una notifica push Firebase. Restituisce True se riuscita."""
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=user_token,
        )
        messaging.send(message)
        print(f"[PUSH] Notifica inviata a {user_token[:10]}…")
        return True
    except Exception as e:
        print(f"[ERROR] Firebase send failed: {e}")
        return False

def log_notification(db: Session, route_id: int, train_code: str, new_status: str):
    """Salva nel DB la notifica inviata (evita duplicati)."""
    log = NotificationLog(
        route_id=route_id,
        train_code=train_code,
        status=new_status,
        sent_at=datetime.datetime.utcnow(),
    )
    db.add(log)
    db.commit()

def check_and_notify(db: Session, route, train, new_status: str):
    """
    Confronta lo stato del treno con l'ultimo noto.
    Se cambia, invia notifica agli utenti della tratta.
    """
    last_log = (
        db.query(NotificationLog)
        .filter_by(route_id=route.id, train_code=train.code)
        .order_by(NotificationLog.sent_at.desc())
        .first()
    )

    if not last_log or last_log.status != new_status:
        title = f"Treno {train.code} → {route.arrival_station}"
        body = f"Stato aggiornato: {new_status}"
        for user in route.users:
            if user.firebase_token:
                send_push_notification(user.firebase_token, title, body)
        log_notification(db, route.id, train.code, new_status)
        print(f"[NOTIFY] {train.code}: {new_status}")
    else:
        print(f"[SKIP] {train.code}: stato invariato ({new_status})")
