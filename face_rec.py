import face_recognition
import numpy as np
import os
import pickle


# for encoding selected student images in known-people folder then storing the encodings in pickle files
def encode_images(known_person_path_file, encoding_path_file, student_dict):
    """Encode the images of students in a class

    This function uses student dict to only encode the images of selected students. The encodings and the student names
    are then stored in pickle files to avoid having to encode again each time face matching is required.

    :param str known_person_path_file: The path of where the images of all students are stored
    :param str encoding_path_file: The path to store the encoded images and student names to
    :param dict student_dict: A dict in the form of {image_filename: student_name}
    :return: None
    """
    known_face_encodings = []
    known_face_names = []

    # loop through all images in known-people folder and encode the images of students in student_dict
    # append each image encoding into known_image_encoding and corresponding student name into known_faces_name
    for file in os.listdir(known_person_path_file):
        if file[0] != '.' and file in student_dict.keys():
            known_image = face_recognition.load_image_file(known_person_path_file + '/' + file)
            known_image_encoding = face_recognition.face_encodings(known_image)[0]
            known_face_encodings.append(known_image_encoding)
            known_face_names.append(student_dict[file])

    # store image encodings and names in pickle files to be stored in /encoding folder
    with open(encoding_path_file + '/encoding.pkl', 'wb') as f:
        pickle.dump(known_face_encodings, f)

    with open(encoding_path_file + '/names.pkl', 'wb') as f:
        pickle.dump(known_face_names, f)


def recognize_faces(encoding_path_file, unknown_image_path_file, unknown_image_filename):
    """Compare the unknown image with the encoded images to try and find a match

    :param str encoding_path_file: The path where the encoded images and student names are stored
    :param str unknown_image_path_file: The path where the image captured from the frontend is stored
    :param str unknown_image_filename: The filename of the image captured from the frontend
    :return: The name of the matched student
    """
    # load the unknown image
    unknown_image = face_recognition.load_image_file(unknown_image_path_file + '/' + unknown_image_filename)

    # get the image encodings and names array from previously pickled files
    with open(encoding_path_file + '/encoding.pkl', 'rb') as f:
        known_face_encodings = pickle.load(f)

    with open(encoding_path_file + '/names.pkl', 'rb') as f:
        known_face_names = pickle.load(f)

    face_locations = face_recognition.face_locations(unknown_image)
    face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

    name = "nobody"

    # matching unknown image with the image encodings
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)

        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            return name

    return name
