
from main import Session
from app.models.db import db  # Adjust the import path to match the actual location of db



session_store = Session()
sessions_collection = db.sessions  