# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.init_db import init_db
from .config import settings
from .routes import health, users, routes_api, trains, stations
from .services.scheduler import start_scheduler

from apscheduler.schedulers.background import BackgroundScheduler

# 🚆 Inizializzazione app FastAPI
app = FastAPI(
    title="TrainWatcher API",
    version="1.0",
    description="Backend per monitoraggio ritardi e cancellazioni treni in tempo reale."
)

# 🌐 Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔒 da limitare in produzione
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔗 Registrazione router
app.include_router(health.router, tags=["Health"])
app.include_router(users.router, tags=["Users"])
app.include_router(routes_api.router, tags=["Routes"])
app.include_router(trains.router, tags=["Trains"])
app.include_router(stations.router, tags=["Stations"])

# 🔄 Variabile globale per lo scheduler
scheduler: BackgroundScheduler | None = None


# 🚀 Startup hooks
@app.on_event("startup")
def on_startup():
    """Inizializza il DB e avvia lo scheduler periodico."""
    global scheduler
    print("[INIT] Avvio TrainWatcher backend...")
    init_db()
    scheduler = start_scheduler(settings.scheduler_interval_minutes)
    print(f"[SCHEDULER] Intervallo: {settings.scheduler_interval_minutes} minuti")
    print("[INIT] Backend pronto ✅")


# 🏠 Endpoint di base
@app.get("/", tags=["System"])
def root():
    """Endpoint di diagnostica base."""
    return {
        "app": "TrainWatcher",
        "version": "1.0",
        "status": "running",
        "scheduler_interval": settings.scheduler_interval_minutes,
        "message": "🚆 TrainWatcher backend attivo e operativo."
    }


# 🕒 Endpoint diagnostico scheduler
@app.get("/scheduler/status", tags=["System"])
def scheduler_status():
    """Restituisce lo stato dello scheduler (job, ultima e prossima esecuzione)."""
    global scheduler
    if not scheduler:
        return {"status": "inactive", "message": "Scheduler non avviato"}

    jobs = scheduler.get_jobs()
    if not jobs:
        return {"status": "no-jobs", "message": "Nessun job registrato nello scheduler"}

    job = jobs[0]
    return {
        "status": "active",
        "job_id": job.id,
        "next_run_time": job.next_run_time,
        "trigger": str(job.trigger),
        "interval_minutes": settings.scheduler_interval_minutes,
    }
