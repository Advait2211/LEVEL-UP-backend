from flask import Blueprint, request, jsonify
from app.models.db import users_collection, events_collection, ngos_collection
from datetime import datetime
from bson import ObjectId

register_bp = Blueprint('register', __name__)

@register_bp.route('/event', methods=['POST'])
def register_event():
    data = request.get_json()
    if not data:
        return "No data provided", 400
    
    event_id = data.get('event_id')
    if not event_id:
        return jsonify({"status": "error", "message": "No event_id provided"}), 400
    
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    print(token)
    if not token:
        return jsonify({"error": "Missing session token"}), 401
    user_data = users_collection.find_one({
        'session_token': token,
        'session_expires': {'$gt': datetime.utcnow()}
    })
    
    user_id = user_data.get('_id') if user_data else None
    print(user_id)
    if not user_id:
        return jsonify({"error": "Invalid session token"}), 401

    if not user_id or not ObjectId.is_valid(user_id):
        return jsonify({"error": "Invalid or missing user_id"}), 400
    
    event = events_collection.find_one({'_id': ObjectId(event_id)})
    if not event:
        return jsonify({"error": "Event not found"}), 404

    if user_id in event.get('participants', []):
        return jsonify({"message": "User already registered for the event"}), 400

    events_collection.update_one(
        {'_id': ObjectId(event_id)},
        {'$push': {'participants': user_id}}
    )

    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$push': {"events_attended": event_id}}
    )

    return jsonify({"message": "User successfully registered for the event"}), 200


@register_bp.route('/ngo', methods=['POST'])
def register_ngo():
    data = request.get_json()
    if not data:
        return "No data provided", 400
    
    ngo_id = data.get('ngo_id')
    if not ngo_id:
        return jsonify({"status": "error", "message": "No event_id provided"}), 400
    
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    print(token)
    if not token:
        return jsonify({"error": "Missing session token"}), 401
    user_data = users_collection.find_one({
        'session_token': token,
        'session_expires': {'$gt': datetime.utcnow()}
    })
    
    user_id = user_data.get('_id') if user_data else None
    print(user_id)
    if not user_id:
        return jsonify({"error": "Invalid session token"}), 401

    if not user_id or not ObjectId.is_valid(user_id):
        return jsonify({"error": "Invalid or missing user_id"}), 400
    
    ngo = ngos_collection.find_one({'_id': ObjectId(ngo_id)})
    if not ngo:
        return jsonify({"error": "NGO not found"}), 404

    if user_id in ngo.get('members', []):
        return jsonify({"message": "User already registered for the NGO"}), 400

    ngos_collection.update_one(
        {'_id': ObjectId(ngo_id)},
        {'$push': {'members': user_id}}
    )
    
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$push': {"ngos_joined": ngo_id}}
    )

    return jsonify({"message": "User successfully registered for the NGO"}), 200