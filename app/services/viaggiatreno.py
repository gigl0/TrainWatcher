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
import requests

def get_station_code(name: str) -> str | None:
    """
    Restituisce il codice Viaggiatreno (es. 'S00035') cercando per nome stazione.
    """
    base_url = "https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/autocompletaStazione/"
    try:
        resp = requests.get(f"{base_url}{name}", timeout=5)
        if not resp.ok or not resp.text.strip():
            print(f"[WARN] Nessuna risposta valida per {name}")
            return None

        # La risposta è testo, es: "TORINO PORTA SUSA|S00035|TORINO P. SUSA|Torino\n..."
        lines = resp.text.strip().split("\n")
        if not lines:
            return None

        first = lines[0].split("|")
        if len(first) >= 2:
            code = first[1].strip()
            return code

        print(f"[WARN] Formato non riconosciuto per {name}: {resp.text}")
        return None

    except Exception as e:
        print(f"[ERROR] get_station_code({name}): {e}")
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
def get_train_status(departure_code: str, train_number: str) -> dict | None:
    """
    Interroga Viaggiatreno per ottenere lo stato di un treno specifico.
    Esempio endpoint:
    https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/andamentoTreno/S00035/4659
    """
    url = f"https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/andamentoTreno/{departure_code}/{train_number}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if not resp.ok:
            print(f"[WARN] get_train_status({train_number}): {resp.status_code}")
            return None

        data = resp.json()
        if not data:
            print(f"[WARN] Nessun dato per treno {train_number}")
            return None

        return data
    except Exception as e:
        print(f"[ERROR] get_train_status({train_number}): {e}")
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