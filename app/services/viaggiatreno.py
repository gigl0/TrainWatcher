import time, requests
from typing import Optional

BASE = "https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno"

def get_station_code(name: str) -> Optional[str]:
    url = f"{BASE}/autocompletaStazione/{name.upper()}"
    r = requests.get(url, timeout=10)
    if r.ok and r.text.strip():
        first = r.text.splitlines()[0]
        return first.split("|")[0] if "|" in first else None
    return None

def get_departures(station_code: str) -> list[dict]:
    ts = int(time.time() * 1000)
    url = f"{BASE}/partenze/{station_code}/{ts}"
    r = requests.get(url, timeout=15)
    return r.json() if r.ok else []

def get_train_status(station_code: str, train_number: str | int) -> Optional[dict]:
    url = f"{BASE}/andamentoTreno/{station_code}/{train_number}"
    r = requests.get(url, timeout=15)
    return r.json() if r.ok else None

def normalize_status(v: dict) -> tuple[str, int]:
    # ritorna (status, delay_minutes)
    provv = v.get("provvedimento", 0)  # 1 = cancellato
    if provv == 1:
        return ("Cancellato", 0)
    delay = int(v.get("ritardo", 0) or 0)
    return ("InOrario" if delay <= 0 else "Ritardo", max(delay, 0))
