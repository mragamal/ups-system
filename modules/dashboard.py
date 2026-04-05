from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from layout import render_page
from auth import current_user

router = APIRouter()

@router.get("/ui", response_class=HTMLResponse)
def dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    content = f"""
        <h1>Dashboard</h1>
        <p>Welcome {user['username']}</p>

        <div class="cards">

            <div class="card">
                <div class="card-title">Dashboard</div>
                <div class="card-desc">Open module workspace</div>
            </div>

            <a href="/ui/clients" class="card-link">
                <div class="card">
                    <div class="card-title">Clients</div>
                    <div class="card-desc">Open module workspace</div>
                </div>
            </a>

            <a href="/ui/users" class="card-link">
                <div class="card">
                    <div class="card-title">Users</div>
                    <div class="card-desc">Manage users and permissions</div>
                </div>
            </a>

        </div>
    """

    return HTMLResponse(render_page("Dashboard", "dashboard", content, user["username"]))