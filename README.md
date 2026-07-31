# Site-57 RP FR — scaffold initial

Ce dépôt contient un scaffold minimal (backend + frontend) pour le projet Site-57 RP FR.

Prerequis:
- Python 3.9+
- virtualenv

Installation & exécution (local):
1. git fetch origin
2. git checkout -b scaffold/site57-backend origin/scaffold/site57-backend || git checkout -b scaffold/site57-backend
3. python -m venv .venv
4. source .venv/bin/activate  # ou .venv\Scripts\activate sur Windows
5. pip install -r requirements.txt
6. Copier .env.example en .env et renseigner les variables (SECRET_KEY, DATABASE_URL, DISCORD_CLIENT_ID etc.)
7. flask db upgrade
8. python app.py
9. Ouvrir http://127.0.0.1:5000

Notes:
- OAuth pour Discord/Roblox est en mode "placeholder" : il faut configurer les credentials et routes côté dev.
- Le bandeau d'alerte est mis à jour via WebSocket (Socket.IO). Les admins peuvent poster une alerte via /admin.
