import requests
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..models import Station

BASE_URL = "https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno"

# ================================
# 🔹 Utility di normalizzazione
# ================================
def normalize_status(train: dict) -> dict:
    """
    Pulisce e normalizza lo stato di un treno Trenitalia.
    """
    delay = int(train.get("ritardo", 0))
    provv = train.get("provvedimento", 0)
    stato = (
        "Cancellato" if provv == 1
        else "Ritardo" if delay > 0
        else "In orario"
    )

    return {
        "train_code": str(train.get("numeroTreno")),
        "status": stato,
        "delay": delay,
    }

# ================================
# 🔹 Codice stazione
# ================================
def get_station_code(name: str) -> Optional[str]:
    """
    Restituisce il codice stazione Viaggiatreno per un nome come 'Pinerolo' o 'Torino Porta Susa'.
    """
    try:
        resp = requests.get(f"{BASE_URL}/cercaStazione/{name}", timeout=8)
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        if not lines or lines[0] == "":
            return None
        # Es: "S01409|Pinerolo"
        return lines[0].split("|")[0]
    except Exception:
        return None

# ================================
# 🔹 Elenco partenze
# ================================
def get_departures(station_code: str) -> List[dict]:
    """
    Restituisce la lista di treni in partenza da una determinata stazione.
    """
    try:
        url = f"{BASE_URL}/partenze/{station_code}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []

# ================================
# 🔹 Stato singolo treno
# ================================
def get_train_status(train_code: str, departure_code: str) -> Optional[dict]:
    """
    Restituisce lo stato corrente di un treno (ritardo, cancellazione, ecc.).
    """
    try:
        url = f"{BASE_URL}/andamentoTreno/{departure_code}/{train_code}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return normalize_status(data)
    except Exception:
        return None

# ================================
# 🔹 Treni per tratta (principale)
# ================================
def get_trains_for_route(departure_code: str, arrival_code: str) -> List[Dict]:
    """
    Restituisce tutti i treni che collegano due stazioni specifiche (es. Pinerolo → Torino Porta Susa).
    """
    departures = get_departures(departure_code)
    if not departures:
        return []

    result = []
    for t in departures:
        dest = t.get("codDestinazione")
        if dest and dest.lower() == arrival_code.lower():
            result.append(normalize_status(t))

    return result

def get_or_cache_station_code(name: str, db: Session) -> str | None:
    """
    Restituisce il codice stazione da cache (DB) o lo scarica da Viaggiatreno e lo memorizza.
    """
    # 🔹 Cerca nel DB
    station = db.query(Station).filter(Station.name.ilike(name)).first()
    if station:
        return station.code

    # 🔹 Se non trovata, chiama le API Viaggiatreno
    code = get_station_code(name)
    if not code:
        return None

    # 🔹 Salva nel DB per le prossime richieste
    new_station = Station(name=name, code=code)
    db.add(new_station)
    db.commit()
    db.refresh(new_station)

    return code