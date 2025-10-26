import os
from fastapi import FastAPI
from .db.init_db import init_db
from .config import settings
from .routes import health, users, routes_api, trains
from .services.scheduler import start_scheduler

app = FastAPI(title="TrainWatcher API")

# Routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(routes_api.router)
app.include_router(trains.router)

@app.on_event("startup")
def on_startup():
    init_db()
    # Avvia scheduler background
    start_scheduler(settings.scheduler_interval_minutes)

@app.get("/")
def root():
    return {"name": "TrainWatcher", "status": "running"}
