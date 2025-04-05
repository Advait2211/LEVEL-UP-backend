from flask import Blueprint, request, jsonify
from app.schema.ngoSchema import NGO
from app.schema.userSchema import User
from bson import ObjectId
from datetime import datetime
from app.models.db import ngos_collection, users_collection

ngo_bp = Blueprint('ngo', __name__)


@ngo_bp.route('/create_ngo', methods=['POST'])
def create_ngo():

    try:
        # Extract user_id from the session token
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
        data = request.get_json()

        if not user_id or not ObjectId.is_valid(user_id):
            return jsonify({"error": "Invalid or missing user_id"}), 400

        owner = User.objects(id=ObjectId(user_id)).first()
        
        if not owner:
            return jsonify({"error": "User not found"}), 404

        ngo = NGO(
            name=data.get('name'),
            description=data.get('description'),
            logo_url=data.get('logo_url'),
            owner_id=owner,
            members=[ObjectId(user_id)],
            outreach_count=data.get('outreach_count'),
            contact_information=data.get('contact_information'),
            location=data.get('location'),
            website=data.get('website'),
            social_media_links=data.get('social_media_links', []),
        )

        result = ngos_collection.insert_one(ngo.to_mongo().to_dict())
        if not result.acknowledged:
            return jsonify({"error": "Failed to create NGO"}), 500
        ngo.id = result.inserted_id
        # Add the NGO to the owner's list of NGOs
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$push": {
                    "ngos_owned": ngo.id,
                    "ngos_joined": ngo.id
                },
                "$set": {"role": "ngo_admin"}
            }
        )

        return jsonify({"message": "NGO created successfully", "ngo_id": str(ngo.id)}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
