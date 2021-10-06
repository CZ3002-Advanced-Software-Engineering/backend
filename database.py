# * --------- IMPORTS --------- *
from bson.objectid import ObjectId
from flask import Flask, request, Response
from flask_cors import CORS, cross_origin
from bson.json_util import dumps, loads
from datetime import date
from flask_pymongo import PyMongo
import os
import time
from face_rec import encode_images, recognize_faces
from PIL import Image
import base64
import io
import shutil

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

# * ---------- Create App --------- *
app = Flask(__name__)

# * ----------MongoDB connect -------*
app.config[
    "MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/database?ssl=true&ssl_cert_reqs=CERT_NONE"
mongo = PyMongo(app)

# * --------MongodbCollection-------*
studentCollection = mongo.db.newStudent
teacherCollection = mongo.db.newTeacher
attendanceCollection = mongo.db.newAttendance
indexCollection = mongo.db.newIndexes


# * -----------Create routes and functions here ---------

# * ----------- General Functions ---------

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


# * ----------- General Routes ---------

# return all documents in specified collection
# args: collection
@app.route("/get_all_items", methods=['GET'])
def getAllItems():
    collection = request.args.get('collection')
    db_collection = getCollection(collection)
    result = db_collection.find({})
    response = Response(dumps(result), mimetype='application/json')
    return response


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


# * ----------- Attendance Routes ---------

# View class attendance for teacher
@app.route("/view_class_attendance", methods=['GET'])
def viewClassAttendance():
    course = request.args.get('course')
    group = request.args.get('group')
    attendance_date = str(request.args.get('date'))

    # get index oid from course and group provided
    index_oid = indexCollection.find_one({'course': course, 'group': group})['_id']

    # find attendance record by index oid and date
    attendance_rec = attendanceCollection.find_one({'index': ObjectId(index_oid), 'date': attendance_date})

    response = Response(dumps(attendance_rec), mimetype='application/json')
    return response


# Take manual attendance
@app.route("/take_attendance/manual", methods=['GET'])
def takeAttendance():
    course = request.args.get('course')
    group = request.args.get('group')
    current_date = str(date.today())
    # current_date = '2021-09-15'

    # get index oid and look for existing attendance rec for today
    index_oid = indexCollection.find_one({'course': course, 'group': group})['_id']
    attendance_rec = attendanceCollection.find_one({'index': index_oid, 'date': current_date})

    # if attendance rec does not exist, create new rec
    if not attendance_rec:
        teacher_oid = teacherCollection.find_one({'indexes_taught': index_oid})['_id']
        student_cursors = studentCollection.find({'indexes_taken': index_oid})
        attendance_rec = genNewAttendance(index_oid, current_date, teacher_oid, student_cursors)

    response = Response(dumps(attendance_rec), mimetype='application/json')
    return response


@app.route('/take_attendance/face', methods=['GET'])
def faceDataPrep():
    start = time.perf_counter()
    course = request.args.get('course')
    group = request.args.get('group')
    current_date = str(date.today())
    # current_date = '2021-09-15'

    # get index oid and look for existing attendance rec for today
    index_oid = indexCollection.find_one({'course': course, 'group': group})['_id']
    attendance_rec = attendanceCollection.find_one({'index': index_oid, 'date': current_date})

    # get all students in the index
    student_list = list(studentCollection.find({'indexes_taken': index_oid}))

    # if attendance rec does not exist, create new rec
    if not attendance_rec:
        teacher_oid = teacherCollection.find_one({'indexes_taught': index_oid})['_id']
        attendance_rec = genNewAttendance(index_oid, current_date, teacher_oid, student_list)

    # place student image filename and student name into dict
    student_dict = {}
    for student in student_list:
        student_dict[student['image']] = student['name']
    encode_images('./known-people', './encoding', student_dict)

    stop = time.perf_counter()
    print(stop - start)
    time.sleep(2)
    response = Response(dumps(attendance_rec), mimetype='application/json')
    return response


@app.route('/face_match', methods=['POST', 'GET'])
def faceMatch():
    start = time.perf_counter()
    data = request.get_json()
    resp = 'No Matches Found.'
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

                name = recognize_faces('./encoding', unknown_img_dir, unknown_img_name)
                if name != 'nobody':
                    resp = name + ' Attendance Taken'
            except:
                pass
    stop = time.perf_counter()
    print(stop - start)
    return resp


# To avoid cors erros
CORS(app, support_credentials=True)

# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
