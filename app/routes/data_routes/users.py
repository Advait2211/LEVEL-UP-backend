from flask import Blueprint, request, jsonify
from datetime import datetime
import re
from app.routes.auth import generate_session_token, User

users_bp = Blueprint('users', __name__)

@users_bp.route('/register-user', methods=['POST'])
def register_user():
    data = request.get_json()

    # Extract fields from request
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    profile_pic_url = data.get('profile_pic_url')
    interests = data.get('interests', [])

    # Validation
    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    if not isinstance(interests, list):
        return jsonify({"error": "Interests must be a list"}), 400
    user = User.find_by_email(email)
    # Check if user already exists
    if user:
        return jsonify({"error": "User already exists"}), 409

    # Insert user
    # user = User(
    #     name=name,
    #     email=email,
    #     profile_pic_url=profile_pic_url,
    #     interests=interests,
    #     created_at=datetime.utcnow()
    # )

    try:
        user = User.create(
            name=name,
            email=email,
            profile_pic_url=profile_pic_url,
            interests=interests,
            password=password,
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

    # result = users_collection.insert_one(user.to_dict())
    # session_token = generate_session_token(str(result.inserted_id), email)
    # session_token  = generate_session_token(result.id, email)

    