# app/routes/auth.py
from flask import Blueprint, jsonify, url_for, session, request, current_app
from app.models.db import  users_collection, bcrypt, oauth
from datetime import datetime, timedelta
import requests
import secrets
from bson import ObjectId
import re

auth_bp = Blueprint('auth', __name__)
GITHUB_API_URL = "https://api.github.com/user/emails"

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

class User:
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.name = user_data.get('name', '')
        self.password_hash = user_data.get('password_hash')
        self.provider = user_data.get('provider', 'email')
        self.profile_pic_url = user_data.get('profile_pic_url', '')
        self.interests = user_data.get('interests', [])

    @staticmethod
    def create(email, password=None, name=None, provider='email', profile_pic_url=None, interests=None):
        if not EMAIL_REGEX.match(email):
            raise ValueError("Invalid email format")
            
        if provider == 'email' and not password:
            raise ValueError("Password required for email signup")

        user_data = {
            'email': email,
            'name': name,
            'created_at': datetime.utcnow(),
            'provider': provider,
            'profile_pic_url': profile_pic_url,
            'interests': interests if interests else []

        }

        if password:
            user_data['password_hash'] = bcrypt.generate_password_hash(password).decode('utf-8')

        result = users_collection.insert_one(user_data)
        return User.find_by_id(result.inserted_id)

    @staticmethod
    def find_by_email(email):
        user_data = users_collection.find_one({'email': email})
        return User(user_data) if user_data else None

    @staticmethod
    def find_by_id(user_id):
        user_data = users_collection.find_one({'_id': ObjectId(user_id)})
        return User(user_data) if user_data else None

    def check_password(self, password):
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)

# Helper functions
def generate_session_token(user_id, email):
    session_token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {
            'session_token': session_token,
            'session_expires': expires_at
        }}
    )
    
    return session_token

def verify_session_token(token):
    if not token:
        return None
    
    user_data = users_collection.find_one({
        'session_token': token,
        'session_expires': {'$gt': datetime.utcnow()}
    })
    
    return User(user_data) if user_data else None

# Routes
@auth_bp.route('/')
def index():
    return jsonify({
        'message': 'Welcome to the authentication module',
        'routes': {
            'google_login': url_for('auth.google_login', _external=True),
            'github_login': url_for('auth.github_login', _external=True),
            'email_signup': url_for('auth.email_signup', _external=True),
            'email_login': url_for('auth.email_login', _external=True)
        }
    })

@auth_bp.route('/signup/email', methods=['POST'])
def email_signup():
    print("Received request for email signup")
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    print("Received data:", data)

    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400

    try:
        if User.find_by_email(email):
            return jsonify({'error': 'Email already exists'}), 409

        user = User.create(
            email=email,
            password=password,
            name=name
        )
        
        session_token = generate_session_token(user.id, email)
        return jsonify({
            'message': 'Signup successful',
            'session_token': session_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/login/email', methods=['POST'])
def email_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.find_by_email(email)
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    session_token = generate_session_token(user.id, email)
    return jsonify({
        'message': 'Login successful',
        'session_token': session_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name
        }
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing authorization token'}), 401

    token = auth_header.split(' ')[1]
    user = verify_session_token(token)
    
    if user:
        users_collection.update_one(
            {'_id': ObjectId(user.id)},
            {'$unset': {
                'session_token': "",
                'session_expires': ""
            }}
        )
    
    return jsonify({'message': 'Logged out successfully'})


def fetch_github_email(access_token):
    """
    Fetches the primary email of the user from GitHub if not provided in user_info.
    """
    headers = {"Authorization": f"token {access_token}"}
    response = requests.get(GITHUB_API_URL, headers=headers)

    if response.status_code == 200:
        emails = response.json()
        primary_email = next((email["email"] for email in emails if email["primary"] and email["verified"]), None)
        return primary_email
    return None

def handle_user_login_or_signup(user_info, access_token):
    """
    Handles user login or signup based on the provided user information.
    If email is null, it fetches the user's primary email from GitHub.
    Uses the User class for consistency.
    """
    if not user_info:
        return jsonify({"error": "Failed to fetch user info"}), 400

    email = user_info.get("email")
    
    # If email is not provided (common with GitHub), fetch it using token
    if not email:
        email = fetch_github_email(access_token)
        if not email:
            return jsonify({"error": "Could not retrieve email from GitHub"}), 400

    # Try to find existing user
    user = User.find_by_email(email)

    if user:
        # Existing user — generate session token
        session_token = generate_session_token(user.id, email)
    else:
        # New user — create using User class
        try:
            user = User.create(
                email=email,
                name=user_info.get("name"),
                provider="oauth"  # You could also use 'google' or 'github' here if desired
            )
            session_token = generate_session_token(user.id, email)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": "Login/signup successful",
        "session_token": session_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "provider": user.provider
        }
    })


# Google login route
@auth_bp.route('/login/google')
def google_login():
    google = oauth.create_client('google')
    redirect_uri = url_for('auth.google_authorize', _external=True)
    print(redirect_uri)
    return google.authorize_redirect(redirect_uri)

# Google authorize route
@auth_bp.route('/login/google/authorize')
def google_authorize():
    google = oauth.create_client('google')
    
    # Debugging: Print the entire request args
    print("Request Args:", request.args)

    token = google.authorize_access_token()

    # Debugging: Check if token is None
    if not token:
        return "Authorization failed: No token received", 400  # Debugging message

    user_info = google.get('userinfo').json()
    return handle_user_login_or_signup(user_info, 'something')


# Github login route
@auth_bp.route('/login/github')
def github_login():
    github = oauth.create_client('github')
    redirect_uri = url_for('auth.github_authorize', _external=True)
    return github.authorize_redirect(redirect_uri)


# Github authorize route
@auth_bp.route('/login/github/authorize')
def github_authorize():
    github = oauth.create_client('github')
    token = github.authorize_access_token()
    user_info = github.get('user').json()
    access_token = token.get("access_token")
    return handle_user_login_or_signup(user_info, access_token)

# Protected route example
@auth_bp.route('/me')
def get_current_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401
    
    token = auth_header.split(' ')[1]
    user = verify_session_token(token)
    
    if not user:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    return jsonify({
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'provider': user.provider
    })
