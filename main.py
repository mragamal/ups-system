from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# استيراد الموديولات
from modules import dashboard, clients, users, login

app = FastAPI()

# static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# include routers
app.include_router(dashboard.router)
app.include_router(clients.router)
app.include_router(users.router)
app.include_router(login.router)

# root redirect
@app.get("/")
def root():
    return RedirectResponse(url="/login")