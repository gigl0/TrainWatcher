import os, json, requests
from ..config import settings

FCM_URL = "https://fcm.googleapis.com/fcm/send"

def send_push(firebase_token: str, title: str, body: str) -> bool:
    # Se non c'è chiave, fai solo log (stub)
    server_key = settings.firebase_server_key
    if not server_key:
        print(f"[NOTIFY:STUB] {title} - {body} -> token {firebase_token[:12]}...")
        return True

    headers = {
        "Authorization": f"key={server_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": firebase_token,
        "notification": {"title": title, "body": body},
        "data": {},
        "priority": "high",
    }
    r = requests.post(FCM_URL, headers=headers, data=json.dumps(payload), timeout=10)
    ok = r.ok
    if not ok:
        print("FCM error:", r.text)
    return ok
