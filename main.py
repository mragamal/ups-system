from fastapi.responses import HTMLResponse
from fastapi import Request


from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Ultra Power Solutions")


# ================= Models =================

class Client(BaseModel):
    id: int
    name: str
    department: str


class Ticket(BaseModel):
    id: int
    client_id: int
    site_name: str
    issue_description: str
    priority: str
    status: str


class WorkOrder(BaseModel):
    id: int
    ticket_id: int
    description: str
    technician_name: str
    driver_name: str
    vehicle_number: str
    status: str


class Trip(BaseModel):
    id: int
    work_order_id: int
    vehicle_number: str
    driver_name: str
    start_time: str
    status: str


# ================= Fake Database =================

clients: List[Client] = []
tickets: List[Ticket] = []
work_orders: List[WorkOrder] = []
trips: List[Trip] = []


# ================= Routes =================

@app.get("/")
def root():
    return {"message": "Ultra Power Solutions System Running"}


# -------- Clients --------

@app.post("/clients")
def create_client(client: Client):
    clients.append(client)
    return {"message": "Client added", "data": client}


@app.get("/clients")
def get_clients():
    return clients


# -------- Tickets --------

@app.post("/tickets")
def create_ticket(ticket: Ticket):
    tickets.append(ticket)
    return {"message": "Ticket added", "data": ticket}


@app.get("/tickets")
def get_tickets():
    return tickets


# -------- Work Orders --------

@app.post("/work-orders")
def create_work_order(work_order: WorkOrder):
    work_orders.append(work_order)
    return {"message": "Work order created", "data": work_order}


@app.get("/work-orders")
def get_work_orders():
    return work_orders


# -------- Trips --------

@app.post("/trips")
def create_trip(trip: Trip):
    trips.append(trip)
    return {"message": "Trip created", "data": trip}


@app.get("/trips")
def get_trips():
    return trips