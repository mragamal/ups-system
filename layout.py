from auth import get_user_modules

def render_page(title: str, active: str, content: str, username: str) -> str:
    user_modules = get_user_modules(username)

    links = []

    if "dashboard" in user_modules:
        cls = "side-link active" if active == "dashboard" else "side-link"
        links.append(f'<a class="{cls}" href="/ui">Dashboard</a>')

    if "clients" in user_modules:
        cls = "side-link active" if active == "clients" else "side-link"
        links.append(f'<a class="{cls}" href="/ui/clients">Clients</a>')

    if "users" in user_modules:
        cls = "side-link active" if active == "users" else "side-link"
        links.append(f'<a class="{cls}" href="/ui/users">Users</a>')

    return f"""
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" href="/static/style.css">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <div class="app-shell">

            <aside class="sidebar">
                <div class="brand-block">
                    <div class="brand-mini">Ultra Power Solutions</div>
                    <div class="brand-title">UPS</div>
                </div>

                <nav class="side-nav">
                    {''.join(links)}
                </nav>

                <a class="side-link logout-link" href="/logout">Logout</a>
            </aside>

            <main class="main-area">
                <header class="topbar">
                    <div class="topbar-left">
                        <div class="topbar-pill">Apps</div>
                        <div class="breadcrumb">Home / {title}</div>
                    </div>

                    <div class="topbar-right">
                        <div class="user-chip">{username}</div>
                    </div>
                </header>

                <section class="page-wrap">
                    {content}
                </section>
            </main>

        </div>
    </body>
    </html>
    """