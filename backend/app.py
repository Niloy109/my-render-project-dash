# backend/app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import os
import json
from typing import Optional

app = FastAPI()

# Data persistence folder
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Load/save helper
def load_json(file_name, default={}):
    path = os.path.join(DATA_DIR, file_name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

def save_json(file_name, data):
    path = os.path.join(DATA_DIR, file_name)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ====== Auth ======
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASS = "admin123"

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    if email == ADMIN_EMAIL and password == ADMIN_PASS:
        return JSONResponse({"status": "success", "message": f"Welcome {email} (admin)!"})
    users = load_json("users.json")
    if email in users and users[email]["password"] == password:
        return JSONResponse({"status": "success", "message": f"Welcome {email}!"})
    return JSONResponse({"status": "error", "message": "Invalid credentials"})

# ====== Users ======
@app.get("/users")
def get_users():
    users = load_json("users.json")
    return users

@app.post("/users/add")
def add_user(email: str = Form(...), password: str = Form(...), is_admin: Optional[bool] = False):
    users = load_json("users.json")
    if email in users:
        return {"status": "error", "message": "User exists"}
    users[email] = {"password": password, "admin": is_admin, "permissions": {}}
    save_json("users.json", users)
    return {"status": "success", "message": f"User {email} added"}

# ====== Permissions ======
@app.get("/permissions/{email}")
def get_permissions(email: str):
    users = load_json("users.json")
    return users.get(email, {}).get("permissions", {})

@app.post("/permissions/{email}/update")
def update_permissions(email: str, perm: str = Form(...), value: bool = Form(...)):
    users = load_json("users.json")
    if email in users:
        users[email]["permissions"][perm] = value
        save_json("users.json", users)
        return {"status": "success"}
    return {"status": "error", "message": "User not found"}

# ====== VPS ======
@app.get("/vps")
def list_vps():
    vps_list = load_json("vps.json")
    return vps_list

@app.post("/vps/create")
def create_vps(name: str = Form(...), owner: Optional[str] = None, root_access: Optional[bool] = False, ipv4: Optional[str] = None):
    vps_list = load_json("vps.json")
    vps_list[name] = {
        "owner": owner,
        "root_access": root_access,
        "ipv4": ipv4 if ipv4 else f"auto.{len(vps_list)+1}.vps.local",
        "status": "stopped"
    }
    save_json("vps.json", vps_list)
    return {"status": "success", "vps": vps_list[name]}

@app.post("/vps/action")
def vps_action(name: str = Form(...), action: str = Form(...)):
    vps_list = load_json("vps.json")
    if name not in vps_list:
        return {"status": "error", "message": "VPS not found"}
    if action == "start":
        vps_list[name]["status"] = "running"
    elif action == "stop":
        vps_list[name]["status"] = "stopped"
    elif action == "restart":
        vps_list[name]["status"] = "restarting"
    elif action == "reboot":
        vps_list[name]["status"] = "running"
    save_json("vps.json", vps_list)
    return {"status": "success", "vps": vps_list[name]}

# ====== Domains ======
@app.get("/domains")
def list_domains():
    domains = load_json("domains.json")
    return domains

@app.post("/domains/add")
def add_domain(domain: str = Form(...), vps_name: str = Form(...)):
    domains = load_json("domains.json")
    domains[domain] = {"vps": vps_name, "status": "pending"}
    save_json("domains.json", domains)
    return {"status": "success", "domain": domains[domain]}

@app.post("/domains/activate")
def activate_domain(domain: str = Form(...)):
    domains = load_json("domains.json")
    if domain in domains:
        domains[domain]["status"] = "activated"
        save_json("domains.json", domains)
        return {"status": "success", "domain": domains[domain]}
    return {"status": "error", "message": "Domain not found"}

# ====== Dashboard UI ======
@app.get("/", response_class=HTMLResponse)
def dashboard():
    users = load_json("users.json")
    vps_list = load_json("vps.json")
    domains = load_json("domains.json")
    return f"""
    <h2>Dashboard Home</h2>
    <p>Users: {list(users.keys())}</p>
    <p>VPS: {list(vps_list.keys())}</p>
    <p>Domains: {list(domains.keys())}</p>
    """
