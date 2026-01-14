# backend/app.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>📊 Dashboard Home</h2>
    <p>Welcome to Render Dashboard</p>
    <ul>
      <li><a href="/vps">VPS List (demo)</a></li>
      <li><a href="/status">Bot & Stats</a></li>
    </ul>
    """

@app.get("/vps")
def vps_list():
    return {"message": "VPS List (demo)"}

@app.get("/status")
def status():
    return {"bot_token_set": bool(os.getenv("DISCORD_TOKEN"))}
