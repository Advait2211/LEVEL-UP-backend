from flask import Blueprint, jsonify, request
from datetime import datetime
from bson import ObjectId
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
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

@get_routes_bp.route('/ngos', methods=['GET'])
def recommend_ngos():
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


    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = convert_object_ids(user)
    
    interests = data.get("interests")

    try:
        recommender = NGORecommender()
        recommendations = recommender.recommend_ngos(interests)
        return jsonify({"status": "success", "data": recommendations}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

class NGORecommender:
    def __init__(self):
        self.users_collection = users_collection
        self.ngos_collection = ngos_collection

    def get_all_ngos(self):
        """Fetch all NGOs and their tags"""
        return list(self.ngos_collection.find({}, {"_id": 1, "name": 1, "tags": 1}))

    def recommend_ngos(self, user_interests, top_n=10):
        if not user_interests:
            return []

        ngos = self.get_all_ngos()
        ngo_ids = [str(ngo["_id"]) for ngo in ngos]
        ngo_names = [ngo["name"] for ngo in ngos]
        ngo_tags = [" ".join(ngo.get("tags", [])) for ngo in ngos]

        # Add user interests as a new "document"
        documents = ngo_tags + [" ".join(user_interests)]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(documents)
        
        # Compute cosine similarity between user interests and each NGO
        user_vector = vectors[-1]  # last one is user
        similarities = cosine_similarity(user_vector, vectors[:-1])[0]

        # Sort and return top N recommendations
        sorted_indices = similarities.argsort()[::-1][:top_n]
        recommended_ngos = [
            {
                "ngo_id": ngo_ids[i],
                "ngo_name": ngo_names[i],
                "score": float(similarities[i])
            }
            for i in sorted_indices if similarities[i] > 0
        ]

        return recommended_ngos

