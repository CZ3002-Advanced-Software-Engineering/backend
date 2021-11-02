# * --------- IMPORTS --------- *
from bson.objectid import ObjectId
from dns.rdatatype import NULL
from flask import Flask, json, request, jsonify, Response
from flask_cors import CORS
from bson import json_util
from datetime import date, datetime
from flask_pymongo import PyMongo
import os
import time
from face_rec import encode_images, recognize_faces
from PIL import Image
import base64
import io
import shutil
import pickle


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(MyEncoder, self).default(obj)


FILE_PATH = os.path.dirname(os.path.realpath(__file__))

# * ---------- Create App --------- *
app = Flask(__name__)
app.json_encoder = MyEncoder

# * ----------MongoDB connect -------*
app.config[
    "MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/demo?ssl=true&ssl_cert_reqs=CERT_NONE"
mongo = PyMongo(app)

# * --------MongodbCollection-------*
studentCollection = mongo.db.student
teacherCollection = mongo.db.teacher
attendanceCollection = mongo.db.attendance
indexCollection = mongo.db.index
docCollection = mongo.db.student_docs


# * ----------- General Functions ---------

def get_collection(collection):
    """Convert given string to mongodb collection

    :param str collection: The collection to retrieve
    :return: The mongodb collection
    """
    if collection == 'student':
        db_collection = studentCollection
    elif collection == 'teacher':
        db_collection = teacherCollection
    elif collection == 'index':
        db_collection = indexCollection
    elif collection == 'attendance':
        db_collection = attendanceCollection
    else:
        db_collection = ''

    return db_collection


def gen_new_attendance(index_oid, attendance_date, teacher_oid, student_cursors):
    """Used by routes to create new attendance entry and insert into db

    :param bson.objectid.ObjectId index_oid: The mongodb object id of the index
    :param str attendance_date: The date of the attendance
    :param bson.objectid.ObjectId teacher_oid: The mongodb object id of the teacher
    :param student_cursors: The list of students that should be in the attendance
    :return: The newly created attendance record
    """
    # consolidate the students into attendance list
    student_list = []
    for student in student_cursors:
        student_list.append({'student': ObjectId(student['_id']),
                             'status': 'pending',
                             'documents': '',
                             'checkintime': '-'})

    # insert new entry into db
    attendance_rec = {
        'index': index_oid,
        'date': attendance_date,
        'teacher': teacher_oid,
        'students': student_list
    }
    attendanceCollection.insert_one(attendance_rec)
    return attendance_rec


def get_attendance(course, group, attendance_date):
    """Retrieve attendance record from database

    :param str course: The course of the attendance record
    :param str group: The group of the attendance record
    :param str attendance_date: The date of the attendance record
    :return: The desired attendance record
    """
    # get index oid from course and group provided
    index_oid = indexCollection.find_one(
        {'course': course, 'group': group})['_id']
    # find attendance record by index oid and date
    attendance_rec = attendanceCollection.find_one(
        {'index': ObjectId(index_oid), 'date': attendance_date})
    return attendance_rec


def update_attendance(index_oid, attendance_date, student_oid, check_in_time, status):
    """Update the attendance status of a student in the database

    :param bson.objectid.ObjectId index_oid: The mongodb object id of the index
    :param str attendance_date: The date of the attendance
    :param bson.objectid.ObjectId student_oid: The mongodb object id of the student
    :param str check_in_time: The check-in time of the student
    :param str status: The attendance status of the student
    :return: None
    """
    attendanceCollection.find_one_and_update(
        {'index': index_oid,
         'date': attendance_date,
         'students.student': student_oid},
        {'$set': {'students.$.checkintime': check_in_time,
                  'students.$.status': status}},
        upsert=False)


# * ----------- General Routes ---------

@app.route("/get_all_items", methods=['GET'])
def get_all_items():
    """Retrieve items from a collection with object ids

    :param str id: The list of object ids of the items to retrieve
    :param str collection: The collection that the ids belong to
    :return: A json of all items retrieved
    """
    docs_list = []
    collection = request.args.get('collection')
    ids_str = request.args.get('id')
    ids_list = json.loads(ids_str)
    db_collection = get_collection(collection)
    for entry in ids_list:
        doc = db_collection.find_one({'_id': ObjectId(entry)})
        docs_list.append(doc)
    return json.dumps(docs_list, default=json_util.default)


# * ----------- View Attendance Routes ---------

@app.route("/view_class_attendance", methods=['GET'])
def view_class_attendance():
    """Retrieve the class attendance list

    :param str course: The course of the attendance record
    :param str group: The group of the attendance record
    :param str date: The date of the attendance record (YYYY-MM-DD)
    :return: A json of the attendance record if found
    """
    course = request.args.get('course')
    group = request.args.get('group')
    attendance_date = str(request.args.get('date'))

    attendance_rec = get_attendance(course, group, attendance_date)
    return jsonify(attendance_rec)


@app.route("/view_student_attendance", methods=['GET'])
def view_student_attendance():
    """Retrieve the student's attendance record

    :param str student_oid: The object id of the student
    :param str course: The course of the attendance record
    :param str group: The group of the attendance record
    :param str date: The date of the attendance record (YYYY-MM-DD)
    :return: A json of the attendance record if found
    """
    student_oid = request.args.get('student_oid')
    course = request.args.get('course')
    group = request.args.get('group')
    attendance_date = str(request.args.get('date'))

    attendance_rec = get_attendance(course, group, attendance_date)
    student_entry = None
    # if attendance rec exists, loop through students to find and retrieve the attendance of student
    if attendance_rec:
        for student_rec in attendance_rec['students']:
            if student_rec['student'] == ObjectId(student_oid):
                student_entry = {
                    'status': student_rec['status'],
                    'documents': student_rec['documents'],
                    'checkintime': student_rec['checkintime']
                }

    return jsonify(student_entry)


@app.route("/view_absentees", methods=['GET'])
def view_absentees():
    """Retrieve all the absentees under a teacher

    :param str teacher_oid: The object id of the teacher
    :return: A json of all the absentees under the teacher
    """
    teacher_oid = request.args.get('teacher_oid')
    indexes_taught = teacherCollection.find_one(
        {'_id': ObjectId(teacher_oid)})['indexes_taught']

    absentees = []
    # if indexes exist, loop through indexes and get all attendances
    if indexes_taught:
        for index_oid in indexes_taught:
            attendances = list(attendanceCollection.find({'index': index_oid}))
            # if attendance records exist, loop through students in each attendance and add absentees to list
            if attendances:
                for attendance_rec in attendances:
                    index_name = indexCollection.find_one(
                        {'_id': attendance_rec['index']})['group']
                    course_name = indexCollection.find_one(
                        {'_id': attendance_rec['index']})['course']
                    for student_rec in attendance_rec['students']:
                        if student_rec['status'] == 'absent':
                            entry = {
                                'id': attendance_rec['_id'],
                                'index': index_name,
                                'course': course_name,
                                'date': attendance_rec['date'],
                                'student': student_rec['student'],
                                'documents': student_rec['documents']
                            }
                            absentees.append(entry)

    return jsonify(absentees)


@app.route("/view_student_absent", methods=['GET'])
def view_student_absent():
    """Retrieve all absent attendance records of a student

    :param str student_oid: The object id of the student
    :return: A json of all the absent attendance records of the student
    """
    student_id = request.args.get('student_oid')
    indexes = studentCollection.find_one(
        {'_id': ObjectId(student_id)})['indexes_taken']

    absentees = []

    if indexes:
        for index in indexes:
            attendances = list(attendanceCollection.find({'index': index}))
            if attendances:
                for attendance_rec in attendances:
                    index_name = indexCollection.find_one(
                        {'_id': attendance_rec['index']})['group']
                    course_name = indexCollection.find_one(
                        {'_id': attendance_rec['index']})['course']
                    for student_rec in attendance_rec['students']:
                        if student_rec['student'] == ObjectId(student_id) and student_rec['status'] == 'absent':
                            entry = {
                                'id': attendance_rec['_id'],
                                'index': index_name,
                                'course': course_name,
                                'date': attendance_rec['date'],
                                'student': student_rec['student'],
                                'documents': student_rec['documents']
                            }
                            absentees.append(entry)
    absentees.sort(key=lambda x: (x.get('course'), x.get('date')))
    return jsonify(absentees)


# * ----------- Manual Attendance Routes ---------

@app.route("/take_attendance/manual", methods=['GET'])
def take_attendance():
    """Create/retrieve an attendance record for a current session

    This route is meant for manual attendance taking. The function attempts to retrieve the session from db and return
    it if found. Otherwise, it creates a new session.

    :param str course: The course of the attendance record
    :param str group: The group of the attendance record
    :return: A json of the attendance record for the requested session
    """
    course = request.args.get('course')
    group = request.args.get('group')
    current_date = str(date.today())

    # get index oid and look for existing attendance rec for today
    index_oid = indexCollection.find_one(
        {'course': course, 'group': group})['_id']
    attendance_rec = attendanceCollection.find_one(
        {'index': index_oid, 'date': current_date})

    # if attendance rec does not exist, create new rec
    if not attendance_rec:
        teacher_oid = teacherCollection.find_one(
            {'indexes_taught': index_oid})['_id']
        student_cursors = studentCollection.find({'indexes_taken': index_oid})
        attendance_rec = gen_new_attendance(
            index_oid, current_date, teacher_oid, student_cursors)

    return jsonify(attendance_rec)


# * ----------- Facial Attendance Routes ---------

@app.route('/take_attendance/face', methods=['GET'])
def face_data_prep():
    """Prepares all data required for taking attendance with using facial recognition

    Create/retrieve attendance record for the current session like the manual route, but with addition of encoding
    images of the students within the class and storing session details for reference by face_match route.

    :param str course: The course of the attendance record
    :param str group: The group of the attendance record
    :return: A json of the attendance record for the requested session
    """
    course = request.args.get('course')
    group = request.args.get('group')
    current_date = str(date.today())

    # get index oid and look for existing attendance rec for today
    index_oid = indexCollection.find_one(
        {'course': course, 'group': group})['_id']
    attendance_rec = attendanceCollection.find_one(
        {'index': index_oid, 'date': current_date})

    # get all students in the index
    student_list = list(studentCollection.find({'indexes_taken': index_oid}))

    # if attendance rec does not exist, create new rec
    if not attendance_rec:
        teacher_oid = teacherCollection.find_one(
            {'indexes_taught': index_oid})['_id']
        attendance_rec = gen_new_attendance(
            index_oid, current_date, teacher_oid, student_list)

    # place student image filename and student name into dict
    student_dict = {}
    for student in student_list:
        student_dict[student['image']] = student['name']

    encode_images('./known-people', './encoding', student_dict)

    # store session details in pickle file
    session_details = {'index_oid': index_oid, 'date': current_date}
    with open('./encoding/session_details.pkl', 'wb') as f:
        pickle.dump(session_details, f)

    time.sleep(2)
    return jsonify(attendance_rec)


@app.route('/face_match', methods=['POST', 'GET'])
def face_match():
    """Match the captured image sent from frontend with encoded student images

    This route should receive a base64 encoded image from the frontend. The image will be used to find a match among the
    encoded student images.

    :return: Student's name if match is found
    """
    # get stored session details
    with open('./encoding/session_details.pkl', 'rb') as f:
        session_details = pickle.load(f)

    data = request.get_json()
    response = 'No Matches Found.'
    unknown_img_dir = './stranger'
    unknown_img_name = 'stranger.jpeg'
    if data:
        if os.path.exists(unknown_img_dir):
            shutil.rmtree(unknown_img_dir)
        if not os.path.exists(unknown_img_dir):
            try:
                os.mkdir(unknown_img_dir)
                time.sleep(1)
                result = data['data']
                b = bytes(result, 'utf-8')
                image = b[b.find(b'/9'):]
                im = Image.open(io.BytesIO(base64.b64decode(image)))
                im.save(unknown_img_dir + '/' + unknown_img_name)

                name = recognize_faces(
                    './encoding', unknown_img_dir, unknown_img_name)

                if name != 'nobody':
                    check_in_time = datetime.now().strftime('%I:%M:%S %p')
                    student_oid = studentCollection.find_one({'name': name})[
                        '_id']
                    update_attendance(session_details['index_oid'], session_details['date'], student_oid,
                                      check_in_time, 'present')
                    response = name + ' Attendance Taken'
            except Exception as e:
                print(e)
                response = 'Error Processing'

    return response


@app.route("/login", methods=['GET'])
def get_user():
    """Retrieve user with username and password

    :param str domain: The domain of the user account
    :param str username: The username of the user
    :param str password: The password of the user
    :return: The user if username and password are valid
    """
    domain = request.args.get('domain')
    db_collection = get_collection(domain)

    username = request.args.get('username')
    password = request.args.get('password')
    user = db_collection.find_one({'username': username, 'password': password})
    if user:
        return jsonify(user)
    else:
        return Response(status=400)


@app.route("/update_attendance", methods=['PUT'])
def get_session():
    """Update attendance record in database when submitting manual attendance

    :param str session_id: The object id of the attendance record
    :param attendance_record: The attendance record made up of student entries from the session
    :return: A json of the updated attendance record
    """
    session_id = json.loads(request.get_data(
        'session_id').decode('UTF-8'))['params']['session_id']
    attendance_record = json.loads(request.get_data(
        'session_id').decode('UTF-8'))['params']['attendance_record']
    print(json.loads(request.get_data(
        'session_id').decode('UTF-8')))
    print('session id', session_id)
    db_collection = attendanceCollection

    for each_student in attendance_record:
        print(each_student)
        student_id = each_student['student']
        attendance = each_student['status']
        if attendance == 'pending':
            attendance = 'absent'
        checkintime = each_student['checkintime']

        db_collection.update_one({'_id': ObjectId(session_id), 'students': {'$elemMatch': {
            'student': ObjectId(student_id)}}},
                                 {'$set': {'students.$.status': attendance, 'students.$.checkintime': checkintime}})

    this_session = db_collection.find_one({'_id': ObjectId(session_id)})
    full_session = db_collection.find_one({'_id': ObjectId(session_id)})
    if this_session:
        return jsonify(full_session)
    else:
        return jsonify(NULL)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload file submitted by student

    :param str studentId: The object id of the student
    :param str attendanceId: The object id of the attendance record
    :return: A success message
    """
    student_id = request.args.get('studentId')
    attendance_id = request.args.get('attendanceId')
    print(student_id)
    print(attendance_id)
    print(request.files)

    if 'document' in request.files:
        document = request.files['document']
        print('document here ', document)
        print('what is document.filename', document.filename)
        mongo.save_file(document.filename, document)
        docCollection.insert_one(
            {'student_id': ObjectId(student_id), 'attendance_id': ObjectId(attendance_id),
             'doc_name': document.filename})
        doc_oid = docCollection.find_one({'student_id': ObjectId(student_id), 'doc_name': document.filename,
                                          'attendance_id': ObjectId(attendance_id)})['_id']
        print('my doc_oid ', doc_oid)
        print('my attendance id ', attendance_id)
        print('my student id ', student_id)
        attendanceCollection.update_one({'_id': ObjectId(attendance_id), 'students': {'$elemMatch': {
            'student': ObjectId(student_id)}}},
                                        {'$set': {'students.$.documents': ObjectId(doc_oid)}})
        print('updated attendance collection')

        return "Uploaded Successfully!"


@app.route('/download/<fileid>')
def get_file(fileid):
    """Direct link to download file by fileid

    :param str fileid: The object id of the file to download
    :return: The requested file if it exists
    """
    try:
        query = {'_id': ObjectId(fileid)}
        print('myfile id ', fileid)
        cursor = docCollection.find_one(query)
        print('my cursor', cursor)
        fileName = cursor['doc_name']
        print('my file name', fileName)
        return mongo.send_file(fileName)
    except:
        return "Unexpected Error!"


# To avoid cors erros
CORS(app, support_credentials=True)

# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
