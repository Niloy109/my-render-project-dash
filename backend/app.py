from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import os, json, uuid, threading
import paramiko

app = FastAPI()
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

# ================= DEFAULT SETTINGS =================
if not os.path.exists(FILES["settings"]):
    save("settings", {"name":"My Dashboard","captcha":False,"smtp":{}})

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
    # Main admin
    if email=="admin@example.com" and password=="admin123":
        SESSION["user"]={"email":email,"admin":True}
        return RedirectResponse("/dashboard",302)
    # Normal users
    users = load("users",{})
    if email in users and users[email]["password"]==password:
        SESSION["user"]={"email":email,"admin":False}
        return RedirectResponse("/dashboard",302)
    return HTMLResponse("Invalid login")

@app.get("/logout")
def logout():
    SESSION.clear()
    return RedirectResponse("/auth/login")

# ================= DASHBOARD =================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    if "user" not in SESSION:
        return RedirectResponse("/auth/login")
    u = SESSION["user"]
    vps = load("vps",{})
    perms = load("perm",{})
    my_vps = {k:v for k,v in vps.items() if u["admin"] or v["owner"]==u["email"]}

    # VPS list
    rows=""
    if not my_vps:
        rows="<p>No VPS associated with your account</p>"
    else:
        for n,v in my_vps.items():
            user_perms = perms.get(u["email"], {"start":True,"stop":True,"restart":True,"ssh":True})
            rows+=f"""
            <div style='border:1px solid #ccc;padding:5px;margin:5px'>
            <b>{n}</b> - {v['status']}<br>
            <form method=post action=/vps/action style=display:inline>
                <input type=hidden name=name value={n}>
                <button name=action value=start {"disabled" if not user_perms.get("start") else ""}>Start</button>
                <button name=action value=stop {"disabled" if not user_perms.get("stop") else ""}>Stop</button>
                <button name=action value=restart {"disabled" if not user_perms.get("restart") else ""}>Restart</button>
                <button name=action value=ssh {"disabled" if not user_perms.get("ssh") else ""}>SSH Console</button>
            </form>
            </div>
            """

    # Admin panels
    admin_panel=""
    if u["admin"]:
        admin_panel=f"""
        <h3>Create VPS</h3>
        <form method=post action=/vps/create>
            <input name=name placeholder="VPS name" required>
            <input name=owner placeholder="Owner email" required>
            <input name=ip placeholder="VPS IP" required>
            <input name=ssh_user placeholder="SSH user" required>
            <input name=ssh_pass placeholder="SSH password" required>
            <button>Create</button>
        </form>
        <h3>Users</h3>
        <form method=post action=/users/create>
            <input name=email placeholder="User email" required>
            <input name=password placeholder="Password" required>
            <button>Create User</button>
        </form>
        <h3>Permissions</h3>
        <p>(Manage user permissions UI)</p>
        <h3>Domains</h3>
        <p>(Domain + IPv4 management UI)</p>
        <h3>Discord Bot</h3>
        <p>(Discord bot panel UI)</p>
        """

    return f"""
    <div style='display:flex'>
        <div style='width:200px;border-right:1px solid #000;padding:10px'>
            <b>MENU</b><br>
            <a href=/dashboard>Dashboard</a><br>
            <a href=#>My VPS</a><br>
            <a href=#>Domains</a><br>
            <a href=#>Discord Bot</a><br>
            {"<a href=#>Permissions</a><br><a href=#>Settings</a>" if u["admin"] else ""}
            <br><a href=/logout>Logout</a>
        </div>
        <div style='flex:1;padding:10px'>
            <h2>Welcome {u['email']} ({'Admin' if u['admin'] else 'User'})</h2>
            {rows}
            {admin_panel}
        </div>
    </div>
    """

# ================= VPS CREATE =================
@app.post("/vps/create")
def create_vps(name:str=Form(...), owner:str=Form(...), ip:str=Form(...), ssh_user:str=Form(...), ssh_pass:str=Form(...)):
    v=load("vps",{})
    v[name]={"owner":owner,"status":"stopped","ip":ip,"ssh_user":ssh_user,"ssh_pass":ssh_pass}
    save("vps",v)
    return RedirectResponse("/dashboard",302)

# ================= VPS ACTION =================
@app.post("/vps/action")
def vps_action(name:str=Form(...), action:str=Form(...)):
    v=load("vps",{})
    if name in v:
        if action=="start": v[name]["status"]="running"
        elif action=="stop": v[name]["status"]="stopped"
        elif action=="restart": v[name]["status"]="restarting"
        elif action=="ssh":
            threading.Thread(target=start_ssh_console, args=(v[name],)).start()
        save("vps",v)
    return RedirectResponse("/dashboard",302)

# ================= SSH CONSOLE (thread) =================
def start_ssh_console(vps):
    ip = vps["ip"]
    user = vps["ssh_user"]
    pwd = vps["ssh_pass"]
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=pwd)
        chan = ssh.invoke_shell()
        chan.send("echo 'SSH console connected'\n")
        while True:
            if chan.recv_ready():
                output = chan.recv(1024).decode()
                print(f"[{vps['owner']}@{vps['ip']}] {output}")
    except Exception as e:
        print("SSH error:", e)

# ================= USERS CREATE =================
@app.post("/users/create")
def create_user(email:str=Form(...), password:str=Form(...)):
    users=load("users",{})
    users[email]={"password":password}
    save("users",users)
    return RedirectResponse("/dashboard",302)
