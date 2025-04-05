from flask import Blueprint, request, jsonify
from app.models.db import events_collection, users_collection, ngos_collection
from datetime import datetime
from bson import ObjectId
from app.schema.eventSchema import Event

events_bp = Blueprint('events', __name__)

@events_bp.route('/events', methods=['POST'])
def add_event():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    ngo_id = data.get('ngo_id')
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
    
    ngo_data = ngos_collection.find_one({'_id': ObjectId(ngo_id)})
    if not ngo_data:
        return jsonify({"error": "NGO not found"}), 404

    owner_id = ngo_data.get('owner_id')
    if not owner_id or owner_id != user_id:
        return jsonify({"error": "User is not authorized to add events for this NGO"}), 403

    name = data.get('name')
    description = data.get('description')
    date = data.get('date')
    location = data.get('location')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    try:
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
    except ValueError:
        return jsonify({'error': 'Invalid datetime format. Use YYYY-MM-DD HH:MM'}), 400


    if not all([name, description, date, location, start_time, end_time]):
        return jsonify({'error': 'Name, description, date, and location are required'}), 400

    try:
        event_date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    event = Event(
        title=name,
        description=description,
        date=event_date,
        location=location,
        start_time=start_time,
        end_time=end_time,
        ngo_id=ObjectId(ngo_id),
    )
    result = events_collection.insert_one(event.to_mongo().to_dict())
    if not result.acknowledged:
        return jsonify({'error': 'Failed to add event'}), 500
    
    # Add the event to the NGO's list of events
    ngos_collection.update_one(
        {"_id": ObjectId(ngo_id)},
        {
            "$push": {
                "events": result.inserted_id
            }
        }
    )
    
    return jsonify({'message': 'Event added successfully', 'event_id': str(result.inserted_id)}), 201