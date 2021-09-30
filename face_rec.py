import face_recognition
import numpy as np
import os
import pickle


class FaceRec:

    def __init__(self, known_person_path_file, unknown_image_path_file, encoding_path_file):
        self.known_person_path_file = known_person_path_file
        self.unknown_images_path_file = unknown_image_path_file
        self.encoding_path_file = encoding_path_file

    # for encoding all images in known-people folder then storing the encodings in a file for faster comparison speed
    def encode_images(self):
        known_face_encodings = []
        known_face_names = []

        # loop through all images in known-people folder and encode the images
        # append each image encoding into known_image_encoding and corresponding filename into known_faces_name
        for file in os.listdir(self.known_person_path_file):
            if file[0] != '.':
                known_image = face_recognition.load_image_file(self.known_person_path_file + '/' + file)
                known_image_encoding = face_recognition.face_encodings(known_image)[0]
                known_face_encodings.append(known_image_encoding)
                known_face_names.append(file)

        # convert the 2 arrays into pickle files to be stored in /encoding folder
        with open(self.encoding_path_file + '/encoding.pkl', 'wb') as f:
            pickle.dump(known_face_encodings, f)

        with open(self.encoding_path_file + '/names.pkl', 'wb') as f:
            pickle.dump(known_face_names, f)

    def recognize_faces(self):
        # load the unknown image
        unknown_image = face_recognition.load_image_file(self.unknown_images_path_file + '/stranger.jpeg')

        # get the image encodings and names array from previously pickled files
        with open(self.encoding_path_file + '/encoding.pkl', 'rb') as f:
            known_face_encodings = pickle.load(f)

        with open(self.encoding_path_file + '/names.pkl', 'rb') as f:
            known_face_names = pickle.load(f)

        face_locations = face_recognition.face_locations(unknown_image)
        face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

        # matching unknown image with the image encodings
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Nobody"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                return name

            return name
