from flask_pymongo import PyMongo
from authlib.integrations.flask_client import OAuth
from flask_bcrypt import Bcrypt
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


oauth = OAuth()  # Using Authlib for OAuth
mongo = PyMongo()
bcrypt = Bcrypt()

def init_extensions(app):
    oauth.init_app(app)
    # mongo.init_app(app)
    # bcrypt.init_app(app)

# Initialize MongoDB client
mongo_client = MongoClient(os.getenv("DATABASE_URL"))
db = mongo_client[os.getenv("MONGO_DB_NAME")]

# Collections
users_collection = db["users"]
