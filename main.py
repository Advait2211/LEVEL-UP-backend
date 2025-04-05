from flask import Flask, jsonify, url_for
from app.routes.auth import auth_bp
from dotenv import load_dotenv
from app.models.db import mongo_client, init_extensions
import os
from datetime import timedelta
from flask_session import Session
from flask_cors import CORS
from app.models.db import oauth
# from authlib.integrations.flask_client import OAuth


load_dotenv()

app = Flask(__name__)
# Configure CORS
CORS(app, resources={
    r"/auth/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Or for all routes (simpler but less secure)
CORS(app, origins=["http://localhost:3000"])

required_vars = [
    "SECRET_KEY",
    "GOOGLE_CLIENT_ID", 
    "GOOGLE_CLIENT_SECRET",
    "GITHUB_CLIENT_ID",
    "GITHUB_CLIENT_SECRET",
    "DATABASE_URL"
]

for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")

# Basic App Config
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# OAuth Config
app.config.update({
    "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
    "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
    "GITHUB_CLIENT_ID": os.getenv("GITHUB_CLIENT_ID"),
    "GITHUB_CLIENT_SECRET": os.getenv("GITHUB_CLIENT_SECRET")
})


# Session Config (must come after extensions initialization)
app.config.update({
    "SESSION_TYPE": "mongodb",
    "SESSION_MONGODB": mongo_client,  # Using mongo_client directly
    "SESSION_MONGODB_DB": os.getenv("MONGO_DB_NAME", "kjsit_hack"),
    "SESSION_PERMANENT": True,
    "SESSION_USE_SIGNER": True,
    "PERMANENT_SESSION_LIFETIME": timedelta(days=7)
})
Session(app)

# oauth = OAuth() 

# Register OAuth clients (your existing code)
google = oauth.register(
    name='google',
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # Correct userinfo endpoint
    client_kwargs={
        'scope': 'openid email profile',  # Ensure 'openid' is included
    },
    server_metadata_url=f'https://accounts.google.com/.well-known/openid-configuration'

)

github = oauth.register(
    name = 'github',
    client_id = app.config["GITHUB_CLIENT_ID"],
    client_secret = app.config["GITHUB_CLIENT_SECRET"],
    access_token_url = 'https://github.com/login/oauth/access_token',
    access_token_params = None,
    authorize_url = 'https://github.com/login/oauth/authorize',
    authorize_params = None,
    api_base_url = 'https://api.github.com/',
    client_kwargs = {'scope': 'user:email'},

)



# Initialize extensions
init_extensions(app)

# oauth.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')

@app.route('/')
def index():
    return jsonify({
        'message': 'Welcome to the main module',
        'routes': {
            'auth': url_for('auth.index', _external=True)
        }
    })

if __name__ == '__main__':
    app.run(debug=True)