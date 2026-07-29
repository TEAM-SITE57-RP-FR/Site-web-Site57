# Applications / Recruitment module for Site57Admin
# Endpoints to manage offers and applications

import os
import json
from flask import request, jsonify, send_from_directory
from datetime import datetime
from werkzeug.utils import secure_filename

# Files & dirs (assumes this module is imported after server sets DATA_DIR)
OFFERS_FILE = os.path.join(os.path.dirname(__file__), "data", "offers.json")
APPLICATIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "applications.json")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg", "zip", "doc", "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file

# Helper load/save

def _load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Ensure dirs/files
os.makedirs(UPLOADS_DIR, exist_ok=True)
if not os.path.exists(OFFERS_FILE):
    _save(OFFERS_FILE, [])
if not os.path.exists(APPLICATIONS_FILE):
    _save(APPLICATIONS_FILE, [])


# Validation helpers

def _allowed(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXT


def init_app(app, config, log_func):
    """Register endpoints on the provided Flask app.
    - app: Flask app
    - config: config dict from server.py
    - log_func: function(event_type, payload)
    """

    @app.route("/api/offers", methods=["GET"])
    def list_offers():
        offers = _load(OFFERS_FILE, [])
        # only return open offers by default
        open_only = request.args.get("open", "true").lower() != "false"
        if open_only:
            offers = [o for o in offers if o.get("status", "open") == "open"]
        return jsonify(offers)

    @app.route("/api/offers", methods=["POST"])
    def create_offer():
        # Admin-only
        token = request.headers.get("X-Admin-Token")
        if not token or token != config.get("admin_token"):
            return jsonify({"error": "Unauthorized"}), 401
        data = request.get_json() or {}
        title = data.get("title")
        description = data.get("description")
        questions = data.get("questions", [])
        if not title:
            return jsonify({"error": "missing title"}), 400
        offers = _load(OFFERS_FILE, [])
        offer = {"id": len(offers) + 1, "title": title, "description": description, "questions": questions, "status": "open", "ts": datetime.utcnow().isoformat() + "Z"}
        offers.insert(0, offer)
        _save(OFFERS_FILE, offers)
        log_func("offer_create", offer)
        return jsonify(offer), 201

    @app.route("/api/offers/<int:offer_id>", methods=["GET"])
    def get_offer(offer_id):
        offers = _load(OFFERS_FILE, [])
        for o in offers:
            if o.get("id") == offer_id:
                return jsonify(o)
        return jsonify({"error": "not found"}), 404

    @app.route("/api/offers/<int:offer_id>", methods=["PUT"])
    def update_offer(offer_id):
        token = request.headers.get("X-Admin-Token")
        if not token or token != config.get("admin_token"):
            return jsonify({"error": "Unauthorized"}), 401
        data = request.get_json() or {}
        offers = _load(OFFERS_FILE, [])
        for i, o in enumerate(offers):
            if o.get("id") == offer_id:
                o.update(data)
                offers[i] = o
                _save(OFFERS_FILE, offers)
                log_func("offer_update", {"id": offer_id, "changes": list(data.keys())})
                return jsonify(o)
        return jsonify({"error": "not found"}), 404

    @app.route("/api/offers/<int:offer_id>", methods=["DELETE"])
    def delete_offer(offer_id):
        token = request.headers.get("X-Admin-Token")
        if not token or token != config.get("admin_token"):
            return jsonify({"error": "Unauthorized"}), 401
        offers = _load(OFFERS_FILE, [])
        new = [o for o in offers if o.get("id") != offer_id]
        if len(new) == len(offers):
            return jsonify({"error": "not found"}), 404
        _save(OFFERS_FILE, new)
        log_func("offer_delete", {"id": offer_id})
        return jsonify({"ok": True})

    # Submit application
    @app.route("/api/applications", methods=["POST"])
    def submit_application():
        # Accept multipart/form-data
        data = {}
        if request.form:
            for k, v in request.form.items():
                data[k] = v
        # expected fields: offer_id, name, email, answers as json string or pairs
        try:
            offer_id = int(data.get("offer_id"))
        except Exception:
            return jsonify({"error": "missing or invalid offer_id"}), 400
        name = data.get("name")
        email = data.get("email")
        if not name or not email:
            return jsonify({"error": "missing name or email"}), 400

        # files
        files_meta = []
        for field in request.files:
            f = request.files.get(field)
            if not f:
                continue
            filename = secure_filename(f.filename)
            if not filename or not _allowed(filename):
                return jsonify({"error": "invalid file type"}), 400
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(0)
            if size > MAX_FILE_SIZE:
                return jsonify({"error": "file too large"}), 400
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            unique_name = f"{timestamp}_{filename}"
            dest = os.path.join(UPLOADS_DIR, unique_name)
            f.save(dest)
            files_meta.append({"field": field, "filename": filename, "path": os.path.relpath(dest, os.path.dirname(__file__))})

        applications = _load(APPLICATIONS_FILE, [])
        app_id = len(applications) + 1
        # collect answers
        answers = {}
        # any form fields starting with answer_ are saved
        for k, v in data.items():
            if k.startswith("answer_"):
                answers[k] = v

        entry = {"id": app_id, "offer_id": offer_id, "name": name, "email": email, "answers": answers, "files": files_meta, "status": "new", "ts": datetime.utcnow().isoformat() + "Z"}
        applications.insert(0, entry)
        _save(APPLICATIONS_FILE, applications)
        log_func("application_submit", {"id": app_id, "offer_id": offer_id, "name": name})

        # optional webhook
        webhook = config.get("application_webhook")
        if webhook:
            try:
                import requests
                requests.post(webhook, json={"text": f"Nouvelle candidature #{app_id} pour offre {offer_id} par {name}"}, timeout=2)
            except Exception:
                pass

        return jsonify({"ok": True, "application_id": app_id}), 201

    @app.route("/api/applications", methods=["GET"])
    def list_applications():
        token = request.headers.get("X-Admin-Token")
        if not token or token != config.get("admin_token"):
            return jsonify({"error": "Unauthorized"}), 401
        offer = request.args.get("offer")
        applications = _load(APPLICATIONS_FILE, [])
        if offer:
            try:
                offer = int(offer)
                applications = [a for a in applications if a.get("offer_id") == offer]
            except Exception:
                pass
        return jsonify(applications)

    @app.route("/api/applications/<int:app_id>", methods=["GET"])
    def get_application(app_id):
        token = request.headers.get("X-Admin-Token")
        if not token or token != config.get("admin_token"):
            return jsonify({"error": "Unauthorized"}), 401
        applications = _load(APPLICATIONS_FILE, [])
        for a in applications:
            if a.get("id") == app_id:
                return jsonify(a)
        return jsonify({"error": "not found"}), 404

    @app.route("/api/applications/<int:app_id>/status", methods=["POST"])
    def set_application_status(app_id):
        token = request.headers.get("X-Admin-Token")
        if not token or token != config.get("admin_token"):
            return jsonify({"error": "Unauthorized"}), 401
        data = request.get_json() or {}
        status = data.get("status")
        comment = data.get("comment")
        applications = _load(APPLICATIONS_FILE, [])
        for i, a in enumerate(applications):
            if a.get("id") == app_id:
                a["status"] = status
                a.setdefault("admin_comments", []).append({"by": "admin", "comment": comment, "ts": datetime.utcnow().isoformat() + "Z"})
                applications[i] = a
                _save(APPLICATIONS_FILE, applications)
                log_func("application_status", {"id": app_id, "status": status})
                return jsonify(a)
        return jsonify({"error": "not found"}), 404

    @app.route("/api/offers/<int:offer_id>/export", methods=["GET"])
    def export_offers_csv(offer_id):
        token = request.headers.get("X-Admin-Token")
        if not token or token != config.get("admin_token"):
            return jsonify({"error": "Unauthorized"}), 401
        applications = _load(APPLICATIONS_FILE, [])
        rows = [a for a in applications if a.get("offer_id") == offer_id]
        # simple CSV generation
        import csv
        from io import StringIO
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(["id", "name", "email", "status", "ts"])  # basic columns
        for r in rows:
            writer.writerow([r.get("id"), r.get("name"), r.get("email"), r.get("status"), r.get("ts")])
        output = si.getvalue()
        return app.response_class(output, mimetype='text/csv')

    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        # This endpoint is public; admin-only could be enforced if desired
        return send_from_directory(UPLOADS_DIR, filename)
