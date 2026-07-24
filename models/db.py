# -*- coding: utf-8 -*-
# ============================================================
# SITE-57 — Modèle de données
# Une seule table clé/valeur : chaque "collection" du site
# (utilisateurs, rôles, articles, annonces, etc.) est stockée
# comme un bloc JSON, exactement comme dans la version Flask —
# ça évite d'avoir à réécrire toute la logique JS existante.
# web2py crée et gère seul le fichier SQLite (databases/storage.sqlite).
# ============================================================

db = DAL('sqlite://storage.sqlite')

db.define_table('kv',
    Field('key', 'string', length=255, unique=True, requires=IS_NOT_EMPTY()),
    Field('value', 'text')
)
