from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db import init_db
from modules import dashboard, clients, users, login

app = FastAPI()

init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(login.router)
app.include_router(dashboard.router)
app.include_router(clients.router)
app.include_router(users.router)