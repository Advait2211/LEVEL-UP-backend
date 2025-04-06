import json
from datetime import datetime
from collections import defaultdict

# Load dataset
with open('synthetic_dataset.json', 'r') as f:
    dataset = json.load(f)

users = dataset["users"]
courses = {course["course_id"]: set(course["tags"]) for course in dataset["courses"]}

# Function to calculate recommendations
def recommend_courses(selected_course_id, user_interactions):
    selected_tags = courses.get(selected_course_id, set())

    # Compute similarity score based on tags
    similarity_scores = {}
    for course_id, tags in courses.items():
        if course_id == selected_course_id:
            continue
        common_tags = selected_tags.intersection(tags)
        similarity_scores[course_id] = len(common_tags)

    # Compute recency weight
    recency_weights = defaultdict(float)
    for interaction in user_interactions:
        course_id = interaction["course_id"]
        timestamp = datetime.strptime(interaction["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")  # FIXED
        hours_ago = (datetime.utcnow() - timestamp).total_seconds() / 3600  # Convert to hours
        weight = 1 / (1 + hours_ago)  # More recent interactions have higher weight
        recency_weights[course_id] += weight

    # Combine scores
    final_scores = {}
    for course_id in similarity_scores:
        final_scores[course_id] = similarity_scores[course_id] + recency_weights.get(course_id, 0)

    # Sort and get top 3 recommendations
    sorted_recommendations = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return sorted_recommendations

# Simulating user interactions
for user in users:
    user_id = user["user_id"]
    print(f"\nRecommendations for {user_id}:")
    
    for interaction in user["recent_interactions"]:
        selected_course = interaction["course_id"]
        recommendations = recommend_courses(selected_course, user["recent_interactions"])
        
        print(f"\nAfter selecting {selected_course}:")
        for course_id, score in recommendations:
            print(f"  - {course_id} (Weight: {score:.2f})")
