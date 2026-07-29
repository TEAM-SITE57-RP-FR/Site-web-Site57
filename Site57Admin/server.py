# Site57Admin/server.py
# Simple Flask-based admin backend for Site57
# Features:
# - Token-based admin auth (header 'X-Admin-Token')
# - Endpoints for announcements, roles, recruitment, bans, logs
# - Endpoint to change site name and links
# - Simulated "start server" launcher
# - Logs saved to logs.json, data saved in memory and persisted to json files for simplicity

# Requirements: pip install flask flask_cors

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
from functools import wraps

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(REPO_ROOT, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

ANNOUNCES_FILE = os.path.join(DATA_DIR, "announces.json")
ROLES_FILE = os.path.join(DATA_DIR, "roles.json")
RECRUITS_FILE = os.path.join(DATA_DIR, "recruits.json")
BANS_FILE = os.path.join(DATA_DIR, "bans.json")
LOGS_FILE = os.path.join(DATA_DIR, "logs.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# A default admin token for initial setup — change this in production!
DEFAULT_ADMIN_TOKEN = "changeme_super_secret_token"

app = Flask(__name__)
CORS(app)

# Helper functions to load/save json

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Initialize storage with defaults
announces = load_json(ANNOUNCES_FILE, [])
roles = load_json(ROLES_FILE, {"developer1234": ["developer"]})
recruits = load_json(RECRUITS_FILE, [])
bans = load_json(BANS_FILE, [])
logs = load_json(LOGS_FILE, [])
config = load_json(CONFIG_FILE, {"site_name": "Site57", "links": {}, "server_running": False, "admin_token": DEFAULT_ADMIN_TOKEN})

# Simple logger

def log(event_type, payload):
    entry = {"ts": datetime.utcnow().isoformat() + "Z", "type": event_type, "payload": payload}
    logs.append(entry)
    save_json(LOGS_FILE, logs)

# Auth decorator

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Token")
        if not token or token != config.get("admin_token"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/api/announces", methods=["GET"])
def get_announces():
    return jsonify(announces)

@app.route("/api/announces", methods=["POST"])
@require_admin
def post_announce():
    data = request.get_json() or {}
    title = data.get("title")
    message = data.get("message")
    if not title or not message:
        return jsonify({"error": "missing title or message"}), 400
    item = {"id": len(announces)+1, "title": title, "message": message, "ts": datetime.utcnow().isoformat() + "Z"}
    announces.insert(0, item)
    save_json(ANNOUNCES_FILE, announces)
    log("announce_create", item)
    return jsonify(item), 201

@app.route("/api/roles", methods=["GET"])
def get_roles():
    return jsonify(roles)

@app.route("/api/roles", methods=["POST"])
@require_admin
def create_role():
    data = request.get_json() or {}
    role_name = data.get("role")
    username = data.get("username")
    if not role_name or not username:
        return jsonify({"error": "missing role or username"}), 400
    user_roles = roles.get(username, [])
    if role_name in user_roles:
        return jsonify({"ok": True, "message": "already has role"})
    user_roles.append(role_name)
    roles[username] = user_roles
    save_json(ROLES_FILE, roles)
    log("role_add", {"username": username, "role": role_name})
    return jsonify({"username": username, "roles": user_roles}), 201

@app.route("/api/recruits", methods=["GET"])
def get_recruits():
    return jsonify(recruits)

@app.route("/api/recruits", methods=["POST"])
@require_admin
def post_recruit():
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description")
    role = data.get("role")
    if not title or not role:
        return jsonify({"error": "missing title or role"}), 400
    item = {"id": len(recruits)+1, "title": title, "role": role, "description": description, "ts": datetime.utcnow().isoformat() + "Z"}
    recruits.insert(0, item)
    save_json(RECRUITS_FILE, recruits)
    log("recruit_create", item)
    return jsonify(item), 201

@app.route("/api/mod/ban", methods=["POST"])
@require_admin
def ban_user():
    data = request.get_json() or {}
    username = data.get("username")
    reason = data.get("reason")
    if not username:
        return jsonify({"error": "missing username"}), 400
    entry = {"username": username, "reason": reason, "ts": datetime.utcnow().isoformat() + "Z"}
    bans.append(entry)
    save_json(BANS_FILE, bans)
    log("ban", entry)
    # In a real integration, we'd also notify Discord or other services here
    return jsonify({"ok": True, "ban": entry}), 201

@app.route("/api/mod/logs", methods=["GET"])
@require_admin
def get_logs():
    return jsonify(logs)

@app.route("/api/config", methods=["GET"])
def get_config():
    public = {k: v for k, v in config.items() if k != "admin_token"}
    return jsonify(public)

@app.route("/api/config", methods=["POST"])
@require_admin
def set_config():
    data = request.get_json() or {}
    if "site_name" in data:
        config["site_name"] = data["site_name"]
    if "links" in data:
        config["links"] = data["links"]
    if "admin_token" in data:
        config["admin_token"] = data["admin_token"]
    save_json(CONFIG_FILE, config)
    log("config_update", {"by": "admin", "changes": list(data.keys())})
    return jsonify({"ok": True, "config": {k: v for k, v in config.items() if k != "admin_token"}})

@app.route("/api/server/start", methods=["POST"])
@require_admin
def start_server():
    # This simulates starting a launcher process; in production you might call a systemd service, docker compose, etc.
    config["server_running"] = True
    save_json(CONFIG_FILE, config)
    log("server_start", {"by": "admin"})
    return jsonify({"ok": True, "server_running": True})

@app.route("/api/server/stop", methods=["POST"])
@require_admin
def stop_server():
    config["server_running"] = False
    save_json(CONFIG_FILE, config)
    log("server_stop", {"by": "admin"})
    return jsonify({"ok": True, "server_running": False})

# Serve a simple admin static page if present
@app.route('/admin/<path:filename>')
@require_admin
def admin_static(filename):
    admin_dir = os.path.join(REPO_ROOT, 'static_admin')
    return send_from_directory(admin_dir, filename)

# Basic health
@app.route('/health')
def health():
    return jsonify({"status": "ok", "server_running": config.get("server_running", False)})

if __name__ == '__main__':
    # Ensure initial files saved
    save_json(ANNOUNCES_FILE, announces)
    save_json(ROLES_FILE, roles)
    save_json(RECRUITS_FILE, recruits)
    save_json(BANS_FILE, bans)
    save_json(LOGS_FILE, logs)
    save_json(CONFIG_FILE, config)

    print("Starting Site57Admin backend on http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
