@app.get("/ui")
def ui():
    return {"status": "ui route works"}