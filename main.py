from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="template")

@app.get("/")
def root():
    return {"message": "Ultra Power Solutions System Running"}

@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})