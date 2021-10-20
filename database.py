# * --------- IMPORTS --------- *
from bson.objectid import ObjectId
from dns.rdatatype import NULL
from flask import Flask, json, request, jsonify, make_response, Response
from flask_cors import CORS, cross_origin
from bson import json_util
from bson.json_util import dumps, loads
from datetime import date, datetime
from flask_pymongo import PyMongo
import os
import time
# from face_rec import encode_images, recognize_faces
# from PIL import Image
import base64
import io
import shutil
import pickle
from json import dumps
from bson.objectid import ObjectId


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

# studentCollection = mongo.db.newStudent
# teacherCollection = mongo.db.newTeacher
# attendanceCollection = mongo.db.newAttendance
# indexCollection = mongo.db.newIndexes
# docCollection = mongo.db.users


# * ----------- General Functions ---------

# translate string to mongo collection
def getCollection(collection):
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


# create new attendance entry and insert into db
def genNewAttendance(index_oid, attendance_date, teacher_oid, student_cursors):
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


# get attendance entry from course, group and date (YYYY-MM-DD string)
def getAttendance(course, group, attendance_date):
    # get index oid from course and group provided
    index_oid = indexCollection.find_one(
        {'course': course, 'group': group})['_id']
    # find attendance record by index oid and date
    attendance_rec = attendanceCollection.find_one(
        {'index': ObjectId(index_oid), 'date': attendance_date})
    return attendance_rec


# update the attendance entry of a student
def updateAttendance(index_oid, attendance_date, student_oid, check_in_time, status):
    attendanceCollection.find_one_and_update(
        {'index': index_oid,
         'date': attendance_date,
         'students.student': student_oid},
        {'$set': {'students.$.checkintime': check_in_time,
                  'students.$.status': status}},
        upsert=False)


# * ----------- General Routes ---------

# return documents with ids in specified collection
# args: collection, ids
@app.route("/get_all_items", methods=['GET'])
def getAllItems():
    docs_list = []
    collection = request.args.get('collection')
    ids = json.loads(request.args.get('id'))
    db_collection = getCollection(collection)
    for entry in ids:
        doc = db_collection.find_one({'_id': ObjectId(entry)})
        docs_list.append(doc)
    # docs_list = list(db_collection.find({'_id': id}))
    return json.dumps(docs_list, default=json_util.default)


# return single document found in specified collection
# args: oid, collection
@app.route("/find_by_oid", methods=['GET'])
def findByOid():
    oid = request.args.get('oid')
    collection = request.args.get('collection')
    db_collection = getCollection(collection)

    if db_collection != '':
        result = db_collection.find_one({'_id': ObjectId(oid)})
        response = Response(dumps(result), mimetype='application/json')
    else:
        response = {}

    return response


# * ----------- View Attendance Routes ---------

# return the attendance list specified by the course, group and date
# args: course, group, date (YYYY-MM-DD string)
@app.route("/view_class_attendance", methods=['GET'])
def viewClassAttendance():
    course = request.args.get('course')
    group = request.args.get('group')
    attendance_date = str(request.args.get('date'))

    attendance_rec = getAttendance(course, group, attendance_date)
    print(attendance_rec)
    return jsonify(attendance_rec)
    # returns null if record does not exist


# return the student's attendance entry specified by the student oid, course, group and date
# args: student_oid, course, group, date (YYYY-MM-DD string)


@app.route("/view_student_attendance", methods=['GET'])
def viewStudentAttendance():
    student_oid = request.args.get('student_oid')
    course = request.args.get('course')
    group = request.args.get('group')
    attendance_date = str(request.args.get('date'))

    attendance_rec = getAttendance(course, group, attendance_date)
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


# return the absentees specified by the teacher's indexes
# args: teacher_oid
@app.route("/view_absentees", methods=['GET'])
def viewAbsentees():
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

# return the attendance list specified by the course, group
# (create new one and return it if none exists for current session)
# args: course, group
@app.route("/take_attendance/manual", methods=['GET'])
def takeAttendance():
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
        attendance_rec = genNewAttendance(
            index_oid, current_date, teacher_oid, student_cursors)

    return jsonify(attendance_rec)


# * ----------- Facial Attendance Routes ---------

# return attendance list like manual route but also encode images of students from the session
# args: course, group
@app.route('/take_attendance/face', methods=['GET'])
def faceDataPrep():
    start = time.perf_counter()
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
        attendance_rec = genNewAttendance(
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

    stop = time.perf_counter()
    print(stop - start)
    time.sleep(2)
    return jsonify(attendance_rec)


# return name of student that matches the image sent to the route
# args: none but must receive base64 encoded image
@app.route('/face_match', methods=['POST', 'GET'])
def faceMatch():
    start = time.perf_counter()

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
                    updateAttendance(session_details['index_oid'], session_details['date'], student_oid,
                                     check_in_time, 'present')
                    response = name + ' Attendance Taken'
            except Exception as e:
                print(e)
                response = 'Error Processing'

    stop = time.perf_counter()
    print(stop - start)
    return response


@app.route("/login", methods=['GET'])
def getUser():
    domain = request.args.get('domain')
    db_collection = getCollection(domain)

    username = request.args.get('username')
    password = request.args.get('password')
    user = db_collection.find_one({'username': username, 'password': password})
    if user:
        return jsonify(user)
    else:
        return Response(status=400)


# put method to update attendance session by objectid

# test comment


@app.route("/update_attendance", methods=['PUT'])
def getSession():
    session_id = json.loads(request.get_data(
        'session_id').decode('UTF-8'))['params']['session_id']
    # session_id = '616c488da51307e040dd213f'
    attendance_record = json.loads(request.get_data(
        'session_id').decode('UTF-8'))['params']['attendance_record']
    # attendance_record = ['615abd43789fb41cf8fd326a:pending',
    #                      '615abd43789fb41cf8fd326e:pending']
    # attendance_record = [{'oid': '615abd43789fb41cf8fd326a', 'status': 'absent'}, {
    #     'oid': '615abd43789fb41cf8fd326e', 'status': 'absent'}]
    print('my attendance record')
    # current_time = datetime.today().strftime("%I:%M:%S %p")
    # print('current time is')
    # print(current_time)
    print(json.loads(request.get_data(
        'session_id').decode('UTF-8')))
    print('session id', session_id)
    # print(attendance_record.split(','))
    # ['615abd43789fb41cf8fd326b:present', ' 615abd43789fb41cf8fd326d:present', ' 615abd43789fb41cf8fd326e:absent']
    db_collection = attendanceCollection

    for each_student in attendance_record:
        # student_id = each_student.split(':')[0]
        # attendance = each_student.split(':')[1]
        print(each_student)
        student_id = each_student['student']
        attendance = each_student['status']
        if attendance == 'pending':
            attendance = 'absent'
        checkintime = each_student['checkintime']
        # print('student id')
        # print(student_id)
        # print('attendance present or absent')
        # print(attendance)

        # print('current status in db')
        # print(db_collection.find_one({'_id': ObjectId(session_id), 'students': {
        #       '$elemMatch': {'student': ObjectId(student_id)}}})['students'][0]['status'])

        db_collection.update_one({'_id': ObjectId(session_id), 'students': {'$elemMatch': {
            'student': ObjectId(student_id)}}},
            {'$set': {'students.$.status': attendance, 'students.$.checkintime': checkintime}})

    this_session = db_collection.find_one({'_id': ObjectId(session_id)})

    # for each_student in this_session['students']:
    #     print(each_student)
    # according to the schema in db currently on 12/10 to access the
    # status of the student present/absent
    # need to use this_session['students'][0]['status']

    full_session = db_collection.find_one({'_id': ObjectId(session_id)})
    if this_session:
        # return jsonify(this_session['students'][0]['status'])
        return jsonify(full_session)
    else:
        return jsonify(NULL)


@app.route("/kevin/manual", methods=['PUT'])
def takeAttendanceKevin():
    # course = request.args.get('course')
    # group = request.args.get('group')
    course = "CZ3002"
    group = "TS1"
    incoming_attendance = ["615abd43789fb41cf8fd3269:present", "615abd43789fb41cf8fd326a:absent",
                           "615abd43789fb41cf8fd326c:present", "615b0e7f9e476147bdc53d31:absent"]
    current_date = str(date.today())
    # current_date = '2021-09-15'

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
        attendance_rec = genNewAttendance(
            index_oid, current_date, teacher_oid, student_cursors)

    for each_student in incoming_attendance:
        student_id = each_student.split(":")[0]
        attendance = each_student.split(":")[1]
        print('student id')
        print(student_id)
        print('attendance present or absent')
        print(attendance)

        attendanceCollection.update_one({'_id': ObjectId(attendance_rec['_id']), 'students': {'$elemMatch': {
            'student': ObjectId(student_id)}}}, {'$set': {'students.$.status': attendance}})

    updated_session = attendanceCollection.find_one(
        {'_id': ObjectId(attendance_rec['_id'])})

    return jsonify(updated_session)


@app.route("/get_data/<id>")
def check(id):
    collection = getCollection(id.split('=')[0])
    oid = id.split('=')[1]
    doc = collection.find_one({'_id': ObjectId(oid)})
    return json.dumps(doc, default=json_util.default)


# Upload file and update documents id into newAttendance
@app.route('/upload', methods=['POST'])
def upload_file():
    # name = request.args.get('name')
    # course = request.args.get('course')
    # group = request.args.get('index')
    # status = request.args.get('status')
    # date = request.args.get('date')
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
        # attendanceCollection.update_one({'_id': ObjectId(attendance_id), 'student': ObjectId(student_id)},
        #                                 {'$set': {'students.$.documents': 'updated document here'}})
        attendanceCollection.update_one({'_id': ObjectId(attendance_id), 'students': {'$elemMatch': {
            'student': ObjectId(student_id)}}},
            {'$set': {'students.$.documents': ObjectId(doc_oid)}})
        print('updated attendance collection')
        # update into attendancelist the id of document in mongodb part not sure

        return "Uploaded Successfully!"


# direct link to download file by fileid
@app.route('/download/<fileid>')
def getfile(fileid):
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


@app.route('/username', methods=['POST'])
def login():
    username = request.json["username"]
    for doc in studentCollection.find():
        if doc['username'] == request.form.get("username", ""):
            return jsonify(username=username)


# To avoid cors erros
CORS(app, support_credentials=True)

# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
