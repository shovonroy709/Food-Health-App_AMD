from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from authlib.integrations.flask_client import OAuth

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_development'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodhealth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID', '1027202675528-r4rrndpsd7ph9pf6gpj5lbo8gf1sklt5.apps.googleusercontent.com')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET', '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')

db = SQLAlchemy(app)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    picture = db.Column(db.String(200))
    calorie_goal = db.Column(db.Integer, default=2000)

class FoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50)) # e.g. Breakfast, Lunch, Dinner, Snack
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/google_login')
def google_login():
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            return "Failed to get user info from Google.", 400
            
        user = User.query.filter_by(google_id=user_info['sub']).first()
        if not user:
            user = User(
                google_id=user_info['sub'],
                name=user_info.get('name', 'User'),
                email=user_info.get('email', ''),
                picture=user_info.get('picture', '')
            )
            db.session.add(user)
            db.session.commit()
            
        session['user'] = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'picture': user.picture
        }
        return redirect(url_for('dashboard'))
    except Exception as e:
        return f"Authentication failed. Make sure you have set valid GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.<br>Error Details: {str(e)}", 400

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_id = session['user']['id']
    user = User.query.get(user_id)
    # Get today's entries
    today = datetime.utcnow().date()
    
    # We'll do a simple python filter for SQLite since date func varies
    all_user_entries = FoodEntry.query.filter_by(user_id=user_id).all()
    entries = [e for e in all_user_entries if e.timestamp.date() == today]
    
    total_calories = sum(entry.calories for entry in entries)
    formatted_now = today.strftime('%B %d, %Y')
    
    return render_template('dashboard.html', user=session['user'], calorie_goal=user.calorie_goal, total_calories=total_calories, entries=entries, now=formatted_now)

@app.route('/data')
def data():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    entries = FoodEntry.query.filter_by(user_id=user_id).order_by(FoodEntry.timestamp.desc()).all()
    
    return render_template('data.html', user=session['user'], entries=entries)

@app.route('/api/add_food', methods=['POST'])
def add_food():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    try:
        new_entry = FoodEntry(
            user_id=session['user']['id'],
            food_name=data['food_name'],
            calories=int(data['calories']),
            category=data.get('category', 'Snack')
        )
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Food logged successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
