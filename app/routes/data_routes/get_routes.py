from flask import Blueprint, jsonify
from bson import ObjectId
from app.models.db import events_collection, users_collection, ngos_collection

# Create a Blueprint for the data routes
get_routes_bp = Blueprint('get_routes', __name__)

# Helper function to recursively convert ObjectIds to strings
def convert_object_ids(doc):
    if isinstance(doc, list):
        return [convert_object_ids(item) for item in doc]
    elif isinstance(doc, dict):
        return {key: convert_object_ids(value) for key, value in doc.items()}
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc

# Route to get all events
@get_routes_bp.route('/events', methods=['GET'])
def get_all_events():
    events = list(events_collection.find())
    events = [convert_object_ids(event) for event in events]
    return jsonify(events), 200

# Route to get all users
@get_routes_bp.route('/users', methods=['GET'])
def get_all_users():
    print('reached here')
    users = list(users_collection.find())
    users = [convert_object_ids(user) for user in users]
    return jsonify(users), 200

# Route to get all NGOs
@get_routes_bp.route('/ngos', methods=['GET'])
def get_all_ngos():
    ngos = list(ngos_collection.find())
    ngos = [convert_object_ids(ngo) for ngo in ngos]
    return jsonify(ngos), 200
