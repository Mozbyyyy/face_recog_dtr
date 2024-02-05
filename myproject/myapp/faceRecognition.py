import face_recognition
import cv2
import os
import dlib
import math
import numpy as np


SHAPE_PREDICTOR_PATH = "myapp/assets/pre-trained/shape_predictor_68_face_landmarks.dat"
KNOWN_FACES_DIR = "myapp/xyryl"
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
THRESHOLD = 0.4

def load_known_faces():
    known_face_encodings = []
    known_face_names = []

    for person_dir in os.listdir(KNOWN_FACES_DIR):
        person_path = os.path.join(KNOWN_FACES_DIR, person_dir)

        if os.path.isdir(person_path):
            for filename in os.listdir(person_path):
                if filename.endswith(".jpg"):
                    person_name = os.path.splitext(filename)[0]
                    image_path = os.path.join(person_path, filename)
                    person_image = face_recognition.load_image_file(image_path)

                    face_encodings = face_recognition.face_encodings(person_image)
                    if face_encodings:
                        person_encoding = face_encodings[0]
                        known_face_encodings.append(person_encoding)
                        known_face_names.append(person_name)

    return known_face_encodings, known_face_names

def calculate_eye_distance(left_eye, right_eye):
    delta_x = right_eye[0] - left_eye[0]
    delta_y = right_eye[1] - left_eye[1]
    angle = math.degrees(math.atan2(delta_y, delta_x))
    return angle

def main():
 
    known_face_encodings, known_face_names = load_known_faces()


    cap = cv2.VideoCapture(0)
    cap.set(3, FRAME_WIDTH)
    cap.set(4, FRAME_HEIGHT)

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)

    while True:
        ret, frame = cap.read()

        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        for face in faces:
            try:
                landmarks = predictor(gray, face)
                left_eye = (landmarks.part(36).x, landmarks.part(36).y)
                right_eye = (landmarks.part(45).x, landmarks.part(45).y)

              
                angle = calculate_eye_distance(left_eye, right_eye)

                reference_distance = np.linalg.norm(np.array(left_eye) - np.array(right_eye))
                distance_between_eyes = np.sqrt((right_eye[0] - left_eye[0]) ** 2 + (right_eye[1] - left_eye[1]) ** 2)
                scale_factor = distance_between_eyes / reference_distance

                rotation_matrix = cv2.getRotationMatrix2D(left_eye, angle, scale_factor)

                aligned_face = cv2.warpAffine(frame, rotation_matrix, (frame.shape[1], frame.shape[0]))

                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                aligned_face = aligned_face[y:y + h, x:x + w]

                aligned_face_rgb = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2RGB)

                face_locations = face_recognition.face_locations(aligned_face_rgb)
                face_encodings = face_recognition.face_encodings(aligned_face_rgb, face_locations)

                found_match = False  # Initialize a flag to keep track of whether a match is found
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=THRESHOLD)
                   
                    if True in matches:
                        
                        first_match_index = matches.index(True)
                        name = known_face_names[first_match_index]
                        found_match = True  # Set the flag to indicate a match is found
                        break  # Break out of the loop if a match is found

                if not found_match:
                    name = "Analyzing Face..." # If no match is found, set the name to "Unknown"
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + x - 20, bottom + y + 20), font, 0.5, (255, 0, 0), 1)

                cv2.rectangle(frame, (left + x, top + y), (right + x, bottom + y), (0, 255, 0), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + x - 20, bottom + y + 20), font, 0.5, (255, 255, 255), 1)
            except Exception as e:
                # Handle any exceptions that may occur during face processing
                print(f"An error occurred: {str(e)}")

        cv2.imshow("Real-Time Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
