from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_socketio import SocketIO, emit
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site57.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins="*")

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models (simple) ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120))
    discord_id = db.Column(db.String(120), unique=True, nullable=True)
    roblox_id = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(40), default='member')  # member / staff / manager / founder
    accreditation = db.Column(db.Integer, default=0)  # 0..5
    avatar_url = db.Column(db.String(250))
    bio = db.Column(db.Text)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    status = db.Column(db.String(50), default='open')  # open / closed / pending

class ModLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(200))
    target = db.Column(db.String(200))
    reason = db.Column(db.Text)

# --- Login loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Placeholder page: redirect to OAuth flows (Discord/Roblox) to implement
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnecté', 'info')
    return redirect(url_for('index'))

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.role not in ['staff', 'manager', 'founder']:
        flash('Accès refusé — accréditation insuffisante', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Exemple: poster une alerte pour le bandeau
        level = request.form.get('level', 'HRP')
        message = request.form.get('message', '')
        payload = {'level': level, 'message': message}
        socketio.emit('banner_update', payload, broadcast=True)
        flash('Alerte envoyée', 'success')
    tickets = Ticket.query.order_by(Ticket.id.desc()).limit(50).all()
    return render_template('admin.html', tickets=tickets)

# API route to create ticket
@app.route('/ticket/create', methods=['POST'])
@login_required
def create_ticket():
    subject = request.form.get('subject')
    content = request.form.get('content')
    t = Ticket(user_id=current_user.id, subject=subject, content=content)
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('index'))

# Endpoint for bot to post alerts
@app.route('/api/bot/alert', methods=['POST'])
def bot_alert():
    secret = os.getenv('BOT_SHARED_SECRET', 'change-me')
    header = request.headers.get('X-BOT-SECRET')
    if not header or header != secret:
        return jsonify({'error':'unauthorized'}), 401
    data = request.get_json() or {}
    level = data.get('level', 'RP')
    message = data.get('message', '')
    socketio.emit('banner_update', {'level': level, 'message': message}, broadcast=True)
    # Log the bot alert into ModLog for audit
    try:
        admin = None
        ml = ModLog(admin_id=admin, action='bot_alert', target='site', reason=message)
        db.session.add(ml)
        db.session.commit()
    except Exception:
        # Non-fatal: ignore logging errors
        pass
    return jsonify({'status':'ok'}), 200

# SocketIO events
@socketio.on('connect')
def on_connect():
    # Client connected
    pass

@socketio.on('request_banner')
def on_request_banner():
    # In a full system, we might load latest banner from DB/cache
    # For scaffold, send a default banner
    emit('banner_update', {'level': 'RP', 'message': 'Code Vert — Tout est stable.'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
