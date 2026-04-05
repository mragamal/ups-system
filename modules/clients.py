from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from layout import render_page
from db import get_conn
from auth import current_user

router = APIRouter()


def init_clients_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            invoice_no TEXT,
            invoice_date TEXT DEFAULT CURRENT_TIMESTAMP,
            subtotal REAL DEFAULT 0,
            tax_percent REAL DEFAULT 0,
            tax_value REAL DEFAULT 0,
            total REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'unpaid',
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoice_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            description TEXT,
            quantity REAL DEFAULT 1,
            unit_price REAL DEFAULT 0,
            line_subtotal REAL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            amount REAL,
            payment_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_clients_db()


def calc_invoice_status(total: float, paid_amount: float) -> str:
    if paid_amount <= 0:
        return "unpaid"
    if paid_amount < total:
        return "partial"
    return "paid"


def next_invoice_no(conn) -> str:
    last_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM invoices").fetchone()[0]
    return f"INV-{last_id + 1:05d}"


@router.get("/ui/clients", response_class=HTMLResponse)
def clients_page(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_conn()

    clients = conn.execute("""
        SELECT * FROM clients ORDER BY id DESC
    """).fetchall()

    invoices = conn.execute("""
        SELECT invoices.*, clients.name AS client_name
        FROM invoices
        LEFT JOIN clients ON clients.id = invoices.client_id
        ORDER BY invoices.id DESC
    """).fetchall()

    total_clients = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    total_invoices = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    total_sales = conn.execute("SELECT COALESCE(SUM(total), 0) FROM invoices").fetchone()[0]
    total_collected = conn.execute("SELECT COALESCE(SUM(paid_amount), 0) FROM invoices").fetchone()[0]
    total_due = float(total_sales or 0) - float(total_collected or 0)

    client_rows = ""
    for c in clients:
        client_rows += f"""
        <tr>
            <td>{c["id"]}</td>
            <td>{c["name"] or ""}</td>
            <td>{c["phone"] or ""}</td>
            <td>{c["email"] or ""}</td>
            <td>{c["address"] or ""}</td>
            <td>
                <a class="btn btn-light" href="/ui/clients/edit/{c["id"]}">Edit</a>
                <a class="btn btn-light" href="/ui/clients/invoices/new?client_id={c["id"]}">Invoice</a>
            </td>
        </tr>
        """

    invoice_rows = ""
    for i in invoices:
        status_class = "badge-unpaid"
        if i["status"] == "paid":
            status_class = "badge-paid"
        elif i["status"] == "partial":
            status_class = "badge-partial"

        due_amount = float(i["total"] or 0) - float(i["paid_amount"] or 0)

        invoice_rows += f"""
        <tr>
            <td>{i["invoice_no"] or f"INV-{i['id']:05d}"}</td>
            <td>{i["client_name"] or "-"}</td>
            <td>{float(i["subtotal"] or 0):.2f}</td>
            <td>{float(i["tax_value"] or 0):.2f}</td>
            <td>{float(i["total"] or 0):.2f}</td>
            <td>{float(i["paid_amount"] or 0):.2f}</td>
            <td>{due_amount:.2f}</td>
            <td><span class="badge {status_class}">{i["status"]}</span></td>
            <td>
                <a class="btn btn-light" href="/ui/clients/invoices/{i["id"]}">View</a>
            </td>
        </tr>
        """

    conn.close()

    content = f"""
        <h1 class="page-title">Clients</h1>
        <div class="page-subtitle">Clients, invoices and payments</div>

        <div class="toolbar">
            <div class="toolbar-left">
                <button class="btn btn-primary" onclick="document.getElementById('add-client-form').scrollIntoView();">New Client</button>
                <a class="btn btn-light" href="/ui/clients/invoices/new">New Invoice</a>
            </div>
        </div>

        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Clients</div>
                <div class="stat-value">{total_clients}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Invoices</div>
                <div class="stat-value">{total_invoices}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Sales</div>
                <div class="stat-value">{float(total_sales):.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Due</div>
                <div class="stat-value">{float(total_due):.2f}</div>
            </div>
        </div>

        <div class="two-cols">

            <div>
                <div class="panel" id="add-client-form">
                    <div class="panel-header">
                        <div class="panel-title">Add Client</div>
                    </div>
                    <div class="panel-body">
                        <form method="post" action="/ui/clients/add" class="form-grid">
                            <div class="form-group">
                                <label>Name</label>
                                <input name="name" required>
                            </div>
                            <div class="form-group">
                                <label>Phone</label>
                                <input name="phone">
                            </div>
                            <div class="form-group">
                                <label>Email</label>
                                <input name="email">
                            </div>
                            <div class="form-group">
                                <label>Address</label>
                                <input name="address">
                            </div>
                            <div class="form-group">
                                <label>Notes</label>
                                <textarea name="notes" rows="3"></textarea>
                            </div>
                            <button class="btn btn-primary" type="submit">Save Client</button>
                        </form>
                    </div>
                </div>
            </div>

            <div>
                <div class="panel" style="margin-bottom:22px;">
                    <div class="panel-header">
                        <div class="panel-title">Clients List</div>
                    </div>
                    <div class="panel-body table-wrap">
                        <table class="erp-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Phone</th>
                                    <th>Email</th>
                                    <th>Address</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {client_rows}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">Invoices</div>
                    </div>
                    <div class="panel-body table-wrap">
                        <table class="erp-table">
                            <thead>
                                <tr>
                                    <th>Invoice No</th>
                                    <th>Client</th>
                                    <th>Subtotal</th>
                                    <th>Tax</th>
                                    <th>Total</th>
                                    <th>Paid</th>
                                    <th>Due</th>
                                    <th>Status</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {invoice_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>
    """

    return HTMLResponse(render_page("Clients", "clients", content, user["username"]))


@router.get("/ui/clients/invoices/new", response_class=HTMLResponse)
def new_invoice_page(request: Request, client_id: int | None = None):
    user = current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_conn()
    clients = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    suggested_invoice_no = next_invoice_no(conn)
    conn.close()

    client_options = ""
    for c in clients:
        selected = "selected" if client_id and c["id"] == client_id else ""
        client_options += f'<option value="{c["id"]}" {selected}>{c["id"]} - {c["name"]}</option>'

    content = f"""
        <h1 class="page-title">New Invoice</h1>
        <div class="page-subtitle">Create quantity-price-tax invoice</div>

        <div class="panel" style="max-width:900px;">
            <div class="panel-header">
                <div class="panel-title">Invoice Entry</div>
            </div>
            <div class="panel-body">
                <form method="post" action="/ui/clients/invoices/create" class="form-grid">

                    <div class="form-group">
                        <label>Client</label>
                        <select name="client_id" required>
                            <option value="">Select client</option>
                            {client_options}
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Invoice Number</label>
                        <input name="invoice_no" value="{suggested_invoice_no}">
                    </div>

                    <div class="form-group">
                        <label>Description</label>
                        <input name="description" required placeholder="Service / Product">
                    </div>

                    <div class="form-group">
                        <label>Quantity</label>
                        <input name="quantity" type="number" step="0.01" value="1" required>
                    </div>

                    <div class="form-group">
                        <label>Unit Price</label>
                        <input name="unit_price" type="number" step="0.01" required>
                    </div>

                    <div class="form-group">
                        <label>Tax %</label>
                        <input name="tax_percent" type="number" step="0.01" value="14" required>
                    </div>

                    <div class="form-group">
                        <label>Notes</label>
                        <textarea name="notes" rows="3"></textarea>
                    </div>

                    <div style="display:flex; gap:12px;">
                        <button class="btn btn-primary" type="submit">Create Invoice</button>
                        <a class="btn btn-light" href="/ui/clients">Back</a>
                    </div>
                </form>
            </div>
        </div>
    """

    return HTMLResponse(render_page("Clients", "clients", content, user["username"]))


@router.post("/ui/clients/invoices/create")
def create_invoice(
    client_id: int = Form(...),
    invoice_no: str = Form(""),
    description: str = Form(...),
    quantity: float = Form(...),
    unit_price: float = Form(...),
    tax_percent: float = Form(14),
    notes: str = Form("")
):
    line_subtotal = float(quantity) * float(unit_price)
    tax_value = line_subtotal * (float(tax_percent) / 100.0)
    total = line_subtotal + tax_value

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO invoices (
            client_id, invoice_no, subtotal, tax_percent, tax_value, total, paid_amount, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        client_id,
        invoice_no.strip(),
        line_subtotal,
        tax_percent,
        tax_value,
        total,
        0,
        "unpaid",
        notes
    ))

    invoice_id = cur.lastrowid

    cur.execute("""
        INSERT INTO invoice_lines (
            invoice_id, description, quantity, unit_price, line_subtotal
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        invoice_id,
        description,
        quantity,
        unit_price,
        line_subtotal
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(f"/ui/clients/invoices/{invoice_id}", status_code=303)


@router.get("/ui/clients/invoices/{invoice_id}", response_class=HTMLResponse)
def invoice_view(invoice_id: int, request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_conn()

    invoice = conn.execute("""
        SELECT invoices.*, clients.name AS client_name, clients.phone AS client_phone, clients.email AS client_email
        FROM invoices
        LEFT JOIN clients ON clients.id = invoices.client_id
        WHERE invoices.id = ?
    """, (invoice_id,)).fetchone()

    lines = conn.execute("""
        SELECT * FROM invoice_lines WHERE invoice_id = ?
    """, (invoice_id,)).fetchall()

    payments = conn.execute("""
        SELECT * FROM payments WHERE invoice_id = ? ORDER BY id DESC
    """, (invoice_id,)).fetchall()

    conn.close()

    if not invoice:
        return RedirectResponse("/ui/clients", status_code=303)

    line_rows = ""
    for line in lines:
        line_rows += f"""
        <tr>
            <td>{line["description"] or ""}</td>
            <td>{float(line["quantity"] or 0):.2f}</td>
            <td>{float(line["unit_price"] or 0):.2f}</td>
            <td>{float(line["line_subtotal"] or 0):.2f}</td>
        </tr>
        """

    payment_rows = ""
    for p in payments:
        payment_rows += f"""
        <tr>
            <td>{p["id"]}</td>
            <td>{float(p["amount"] or 0):.2f}</td>
            <td>{p["payment_date"]}</td>
        </tr>
        """

    due_amount = float(invoice["total"] or 0) - float(invoice["paid_amount"] or 0)

    content = f"""
        <h1 class="page-title">Invoice {invoice["invoice_no"] or f"INV-{invoice['id']:05d}"}</h1>
        <div class="page-subtitle">Client: {invoice["client_name"] or "-"}</div>

        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Subtotal</div>
                <div class="stat-value">{float(invoice["subtotal"] or 0):.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Tax</div>
                <div class="stat-value">{float(invoice["tax_value"] or 0):.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total</div>
                <div class="stat-value">{float(invoice["total"] or 0):.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Due</div>
                <div class="stat-value">{due_amount:.2f}</div>
            </div>
        </div>

        <div class="two-cols">

            <div>
                <div class="panel" style="margin-bottom:22px;">
                    <div class="panel-header">
                        <div class="panel-title">Invoice Details</div>
                    </div>
                    <div class="panel-body">
                        <div><b>Invoice No:</b> {invoice["invoice_no"] or f"INV-{invoice['id']:05d}"}</div>
                        <div style="margin-top:8px;"><b>Date:</b> {invoice["invoice_date"]}</div>
                        <div style="margin-top:8px;"><b>Client:</b> {invoice["client_name"] or "-"}</div>
                        <div style="margin-top:8px;"><b>Phone:</b> {invoice["client_phone"] or "-"}</div>
                        <div style="margin-top:8px;"><b>Email:</b> {invoice["client_email"] or "-"}</div>
                        <div style="margin-top:8px;"><b>Tax %:</b> {float(invoice["tax_percent"] or 0):.2f}</div>
                        <div style="margin-top:8px;"><b>Status:</b> {invoice["status"]}</div>
                        <div style="margin-top:8px;"><b>Notes:</b> {invoice["notes"] or "-"}</div>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">Register Payment</div>
                    </div>
                    <div class="panel-body">
                        <form method="post" action="/ui/clients/pay" class="form-grid">
                            <input type="hidden" name="invoice_id" value="{invoice["id"]}">
                            <div class="form-group">
                                <label>Amount</label>
                                <input name="amount" type="number" step="0.01" required>
                            </div>
                            <button class="btn btn-success" type="submit">Save Payment</button>
                        </form>
                    </div>
                </div>
            </div>

            <div>
                <div class="panel" style="margin-bottom:22px;">
                    <div class="panel-header">
                        <div class="panel-title">Invoice Lines</div>
                    </div>
                    <div class="panel-body table-wrap">
                        <table class="erp-table">
                            <thead>
                                <tr>
                                    <th>Description</th>
                                    <th>Qty</th>
                                    <th>Unit Price</th>
                                    <th>Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>
                                {line_rows}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">Payments</div>
                    </div>
                    <div class="panel-body table-wrap">
                        <table class="erp-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Amount</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {payment_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>
    """

    return HTMLResponse(render_page("Clients", "clients", content, user["username"]))


@router.post("/ui/clients/add")
def add_client(
    name: str = Form(...),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    notes: str = Form("")
):
    conn = get_conn()
    conn.execute(
        "INSERT INTO clients (name, phone, email, address, notes) VALUES (?, ?, ?, ?, ?)",
        (name, phone, email, address, notes)
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/ui/clients", status_code=303)


@router.post("/ui/clients/pay")
def pay(invoice_id: int = Form(...), amount: float = Form(...)):
    conn = get_conn()

    invoice = conn.execute(
        "SELECT * FROM invoices WHERE id = ?",
        (invoice_id,)
    ).fetchone()

    if invoice:
        new_paid = float(invoice["paid_amount"] or 0) + float(amount)
        new_status = calc_invoice_status(float(invoice["total"] or 0), new_paid)

        conn.execute(
            "INSERT INTO payments (invoice_id, amount) VALUES (?, ?)",
            (invoice_id, amount)
        )

        conn.execute(
            "UPDATE invoices SET paid_amount = ?, status = ? WHERE id = ?",
            (new_paid, new_status, invoice_id)
        )

    conn.commit()
    conn.close()

    return RedirectResponse(f"/ui/clients/invoices/{invoice_id}", status_code=303)


@router.get("/ui/clients/edit/{client_id}", response_class=HTMLResponse)
def edit_client_page(client_id: int, request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_conn()
    client = conn.execute(
        "SELECT * FROM clients WHERE id = ?",
        (client_id,)
    ).fetchone()
    conn.close()

    if not client:
        return RedirectResponse("/ui/clients", status_code=303)

    content = f"""
        <h1 class="page-title">Edit Client</h1>
        <div class="page-subtitle">Update client information</div>

        <div class="panel" style="max-width:700px;">
            <div class="panel-header">
                <div class="panel-title">Client #{client["id"]}</div>
            </div>
            <div class="panel-body">
                <form method="post" action="/ui/clients/edit/{client["id"]}" class="form-grid">
                    <div class="form-group">
                        <label>Name</label>
                        <input name="name" value="{client["name"] or ""}" required>
                    </div>
                    <div class="form-group">
                        <label>Phone</label>
                        <input name="phone" value="{client["phone"] or ""}">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input name="email" value="{client["email"] or ""}">
                    </div>
                    <div class="form-group">
                        <label>Address</label>
                        <input name="address" value="{client["address"] or ""}">
                    </div>
                    <div class="form-group">
                        <label>Notes</label>
                        <textarea name="notes" rows="4">{client["notes"] or ""}</textarea>
                    </div>

                    <div style="display:flex; gap:12px;">
                        <button class="btn btn-primary" type="submit">Save Changes</button>
                        <a class="btn btn-light" href="/ui/clients">Back</a>
                    </div>
                </form>
            </div>
        </div>
    """

    return HTMLResponse(render_page("Clients", "clients", content, user["username"]))


@router.post("/ui/clients/edit/{client_id}")
def edit_client_save(
    client_id: int,
    name: str = Form(...),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    notes: str = Form("")
):
    conn = get_conn()
    conn.execute("""
        UPDATE clients
        SET name = ?, phone = ?, email = ?, address = ?, notes = ?
        WHERE id = ?
    """, (name, phone, email, address, notes, client_id))
    conn.commit()
    conn.close()

    return RedirectResponse("/ui/clients", status_code=303)