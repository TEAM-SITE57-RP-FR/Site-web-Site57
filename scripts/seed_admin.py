# Seed script pour développement : crée un compte admin non sécurisé

from app import db, User

admin = User(username='admin_seed', email='admin@example.com', role='founder', accreditation=5)
try:
    db.session.add(admin)
    db.session.commit()
    print('Compte admin_seed créé')
except Exception as e:
    print('Erreur:', e)
