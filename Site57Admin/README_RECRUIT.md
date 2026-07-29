Site57

Module recrutement / candidatures ajouté.

Démarrage rapide:
- Installer dépendances: pip install flask flask_cors requests
- Depuis le dossier Site57Admin: python server.py
- Pages:
  - Public: /admin/static_member/apply.html  (or open Site57Admin/static_member/apply.html)
  - Admin: /Site57Admin/static_admin/recruits.html

API endpoints:
- Offers: GET /api/offers  POST /api/offers (admin) GET/PUT/DELETE /api/offers/<id>
- Applications: POST /api/applications  GET /api/applications (admin) GET /api/applications/<id> POST /api/applications/<id>/status
- Export: /api/offers/<id>/export
- Uploads served at /uploads/<filename>

Sécurité:
- Admin routes protégés par X-Admin-Token (config.json admin_token)
- Changez le token via /api/config

Notes:
- Uploads stockés dans Site57Admin/data/uploads/
- Webhook de notification configurable via config key 'application_webhook'
