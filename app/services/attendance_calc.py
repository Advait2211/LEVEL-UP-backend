import sys
import os
import time
import base64
from flask import request

from app.models.db import events_collection, users_collection, ngos_collection
from app.services.face_rec import FaceRecognitionService
from flask import Blueprint, jsonify
from bson import ObjectId

# start_time = time.time()
fc = FaceRecognitionService()

"""
1. event id (each event has how many number of participants)
2. user id (name, profile photo)
3. events (start photo, end photo)

for execution of 1 image it takes on average 2 seconds
it will take  2 * n ^ m for execution of all images
n = number of participants
m = number of events



for i in range(0, 5):
    for j in range(0, 5):
        print(j)
        fc.is_face_present("face_photo.jpg", f"photo{j}.png")

        

end_time = time.time()
execution_time = end_time - start_time
print(f"Execution time: {execution_time} seconds")

"""

attendance_calc_bp = Blueprint('attendance_calc', __name__)

@attendance_calc_bp.route('/process_event', methods=['POST'])
def process_event():
    # Save the images passed from the frontend to the database
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    event_id = data.get('event_id')
    start_photo_base64 = data.get('start_photo')
    end_photo_base64 = data.get('end_photo')

    if not event_id or not start_photo_base64 or not end_photo_base64:
        return jsonify({"status": "error", "message": "Missing event_id or photos"}), 400

    # Update the event document with the provided images
    events_collection.update_one(
        {"_id": ObjectId(event_id)},
        {"$set": {
            "start_photo_url": start_photo_base64,
            "end_photo_url": end_photo_base64
        }}
    )

    event = events_collection.find_one({"_id": ObjectId(event_id)})
    if not event:
        return jsonify({"status": "error", "message": "Event not found"}), 404

    start_image_url = event.get('start_photo_url')
    end_image_url = event.get('end_photo_url')
    if not start_image_url or not end_image_url:
        return jsonify({"status": "error", "message": "No image URLs found"}), 400

    def base64_to_image(base64_str, output_path):
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        # print(len(base64_str))
        image_data = base64.b64decode(base64_str)
        with open(output_path, "wb") as f:
            f.write(image_data)
        print(f"Saved to {output_path}")

    base64_to_image(start_image_url, "./app/services/start_photo.png")
    base64_to_image(end_image_url, "./app/services/end_photo.png")

    participants = event.get('participants')

    if not participants:
        return jsonify({"status": "error", "message": "No participants"})
    
    for p in participants:
        user = users_collection.find_one({"_id": ObjectId(p)})
        if not user:
            continue
        user_face_url = user.get('profile_pic_url')
        if not user_face_url:
            continue
        print(user_face_url)
        base64_to_image(user_face_url, "./app/services/user_face.png")
        status1 = fc.is_face_present("./app/services/user_face.png", "./app/services/start_photo.png")
        status2 = fc.is_face_present("./app/services/user_face.png", "./app/services/end_photo.png")

        if status1 and status2:
            value  = 100 # full duration of the event
        if status1 and not status2 or not status1 and status2:
            value = 40
        else:
            value = 0
        
        start_time = event.get('start_time')
        end_time = event.get('end_time')

        if not start_time or not end_time:
            return jsonify({"status": "error", "message": "Event start_time or end_time is missing"}), 400

        duration = (end_time - start_time).total_seconds() / 3600  # Convert seconds to hours
        ngo = event.get('ngo_id')

        # update events collection per user
        events_collection.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": {f"attendance.{ObjectId(p)}": value * duration / 100}}
        )

        # update users per event
        users_collection.update_one(
            {"_id": ObjectId(p)},
            {"$set": {f"attendance_summary.{ObjectId(ngo)}.{event_id}": value * duration / 100}}
        )
    
        # # Fetch and print user attendance for the given event_id
        # attendance_data = events_collection.find_one(
        #     {"_id": ObjectId(event_id)},
        #     {"attendance": 1, "_id": 0}
        # )

        # if not attendance_data or "attendance" not in attendance_data:
        #     return jsonify({"status": "error", "message": "No attendance data found"}), 404

        # print("User Attendance for Event:", attendance_data["attendance"])



    return jsonify({"status": "success", "message": "Image saved and event processed"}), 200