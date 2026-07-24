# -*- coding: utf-8 -*-
# ============================================================
# SITE-57 — Contrôleur principal
# Sert les deux pages (Membre / Admin) et expose une petite
# API JSON utilisée par site57_core.js pour lire/écrire les
# données du site.
# ============================================================
import json


def index():
    redirect(URL('static', 'site57_index.html'))


def membre():
    redirect(URL('static', 'site57_membre.html'))


def admin():
    redirect(URL('static', 'site57_admin.html'))


# ------------------------------------------------------------
# API de stockage clé/valeur
# ------------------------------------------------------------
def kv_get():
    response.headers['Content-Type'] = 'application/json'
    key = request.vars.key
    row = db.kv(key=key)
    if not row:
        raise HTTP(404, json.dumps({'error': 'not_found'}), **{'Content-Type': 'application/json'})
    return json.dumps({'key': key, 'value': row.value})


def kv_set():
    response.headers['Content-Type'] = 'application/json'
    key = request.vars.key
    value = request.vars.value or ''
    if not key:
        raise HTTP(400, json.dumps({'error': 'missing_key'}), **{'Content-Type': 'application/json'})
    row = db.kv(key=key)
    if row:
        row.update_record(value=value)
    else:
        db.kv.insert(key=key, value=value)
    db.commit()
    return json.dumps({'key': key, 'value': value})


def kv_delete():
    response.headers['Content-Type'] = 'application/json'
    key = request.vars.key
    row = db.kv(key=key)
    existed = bool(row)
    if row:
        row.delete_record()
        db.commit()
    return json.dumps({'key': key, 'deleted': existed})


def kv_list():
    response.headers['Content-Type'] = 'application/json'
    prefix = request.vars.prefix or ''
    rows = db(db.kv.key.like(prefix + '%')).select(db.kv.key)
    return json.dumps({'keys': [r.key for r in rows]})
