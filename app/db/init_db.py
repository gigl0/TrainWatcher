from .session import engine
from ..models import Base

def init_db() -> None:
    print("[INIT_DB] Avvio creazione tabelle...")
    Base.metadata.create_all(bind=engine)
    print("[INIT_DB] Tabelle create (se non esistevano).")

if __name__ == "__main__":
    init_db()
