from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# modules
from modules import dashboard, users, login, inventory, accounting

app = FastAPI()

# static files (css/js)
app.mount("/static", StaticFiles(directory="static"), name="static")


# =========================
# ROUTERS
# =========================
app.include_router(login.router)
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(inventory.router)
app.include_router(accounting.router)


# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"msg": "Merza ERP System Running 🚀"}