from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import json, os, uuid

app = FastAPI()

# ================= PATH =================
BASE = "backend/data"
os.makedirs(BASE, exist_ok=True)

FILES = {
    "users": f"{BASE}/users.json",
    "vps": f"{BASE}/vps.json",
    "perm": f"{BASE}/permissions.json",
    "discord": f"{BASE}/discord.json",
    "domains": f"{BASE}/domains.json",
    "settings": f"{BASE}/settings.json"
}

def load(name, default):
    f = FILES[name]
    if os.path.exists(f):
        return json.load(open(f))
    return default

def save(name, data):
    json.dump(data, open(FILES[name], "w"), indent=2)

SESSION = {}

# ================= DEFAULT =================
if not os.path.exists(FILES["settings"]):
    save("settings", {"name":"My Dashboard","captcha":False})

# ================= LOGIN =================
@app.get("/auth/login", response_class=HTMLResponse)
def login_page():
    return """
    <h2>Login</h2>
    <form method=post>
    <input name=email placeholder=Email><br><br>
    <input type=password name=password placeholder=Password><br><br>
    <button>Login</button>
    </form>
    """

@app.post("/auth/login")
def login(email: str = Form(...), password: str = Form(...)):
    if email=="admin@example.com" and password=="admin123":
        SESSION["user"]={"email":email,"admin":True}
        return RedirectResponse("/dashboard",302)
    return HTMLResponse("Invalid login")

# ================= DASHBOARD =================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    if "user" not in SESSION:
        return RedirectResponse("/auth/login")

    u = SESSION["user"]
    vps = load("vps",{})
    my = {k:v for k,v in vps.items() if u["admin"] or v["owner"]==u["email"]}

    rows=""
    if not my:
        rows="<p><b>No VPS associated with your account</b></p>"
    else:
        for n,v in my.items():
            rows+=f"""
            <div>
            <b>{n}</b> — {v['status']}
            <form method=post action=/vps/action style=display:inline>
            <input type=hidden name=name value={n}>
            <button name=action value=start>Start</button>
            <button name=action value=stop>Stop</button>
            <button name=action value=restart>Restart</button>
            </form>
            </div><hr>
            """

    admin=""
    if u["admin"]:
        admin="""
        <h3>Create VPS</h3>
        <form method=post action=/vps/create>
        <input name=name placeholder="VPS name">
        <input name=owner placeholder="Owner email">
        <button>Create</button>
        </form>
        """

    return f"""
    <style>
    body{{font-family:Arial}}
    #side{{width:200px;float:left}}
    #main{{margin-left:210px}}
    </style>

    <div id=side>
    <b>MENU</b><hr>
    <a href=/dashboard>Dashboard</a><br>
    <a>My VPS</a><br>
    <a>Domains</a><br>
    <a>Discord Bot</a><br>
    {"<a>Permissions</a><br><a>Settings</a>" if u["admin"] else ""}
    <br><a href=/logout>Logout</a>
    </div>

    <div id=main>
    <h2>Welcome {u["email"]}</h2>
    {rows}
    {admin}
    </div>
    """

# ================= VPS =================
@app.post("/vps/create")
def create_vps(name:str=Form(...), owner:str=Form(...)):
    v=load("vps",{})
    v[name]={"owner":owner,"status":"stopped"}
    save("vps",v)
    return RedirectResponse("/dashboard",302)

@app.post("/vps/action")
def vps_action(name:str=Form(...), action:str=Form(...)):
    v=load("vps",{})
    if name in v:
        if action=="start": v[name]["status"]="running"
        if action=="stop": v[name]["status"]="stopped"
        if action=="restart": v[name]["status"]="restarting"
        save("vps",v)
    return RedirectResponse("/dashboard",302)

@app.get("/logout")
def logout():
    SESSION.clear()
    return RedirectResponse("/auth/login")
