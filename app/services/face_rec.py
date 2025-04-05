import face_recognition
# if not running, use pip install setuptools
print(face_recognition.__file__)

class FaceRecognitionService:
    def __init__(self, tolerance=0.5):
        self.tolerance = tolerance

    def is_face_present(self, user_face_path, group_image_path):
        # Load the user's face image
        user_image = face_recognition.load_image_file(user_face_path)
        user_encodings = face_recognition.face_encodings(user_image)

        if len(user_encodings) == 0:
            print("No face found in user image.")
            return False

        user_encoding = user_encodings[0]

        # Load the group image (event photo)
        group_image = face_recognition.load_image_file(group_image_path)
        group_encodings = face_recognition.face_encodings(group_image)

        if len(group_encodings) == 0:
            print("No face found in group image.")
            return False

        # Compare each face in the group photo with the user face
        results = face_recognition.compare_faces(group_encodings, user_encoding, self.tolerance)

        # Return True if any face matches
        return any(results)
    
# def is_face_present(user_face_path, group_image_path, tolerance=0.5):
#     # Load the user's face image
#     user_image = face_recognition.load_image_file(user_face_path)
#     user_encodings = face_recognition.face_encodings(user_image)

#     if len(user_encodings) == 0:
#         print("No face found in user image.")
#         return False
    
#     user_encoding = user_encodings[0]

#     # Load the group image (event photo)
#     group_image = face_recognition.load_image_file(group_image_path)
#     group_encodings = face_recognition.face_encodings(group_image)

#     if len(group_encodings) == 0:
#         print("No face found in group image.")
#         return False

#     # Compare each face in the group photo with the user face
#     results = face_recognition.compare_faces(group_encodings, user_encoding, tolerance)

#     # Return True if any face matches
#     return any(results)

fc = FaceRecognitionService()
# print(fc.is_face_present("face_photo.jpg", "photo4.png"))
