from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.db import users_collection, ngos_collection
from flask import Blueprint, request, jsonify

recommender_bp = Blueprint('recommender', __name__)

@recommender_bp.route('/', methods=['POST'])
def recommend_ngos():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    
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

