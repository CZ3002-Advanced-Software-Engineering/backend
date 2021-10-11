# * --------- IMPORTS --------- *
from bson.objectid import ObjectId
from flask import Flask, json, request, jsonify, make_response, Response
from flask_cors import CORS, cross_origin
from bson.json_util import dumps, loads
from datetime import date
import os
from flask_pymongo import PyMongo
from json import dumps
import flask
from bson import json_util
from bson.objectid import ObjectId

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
        print(result)
        #response = Response(dumps(result), mimetype='application/json')
        #response = json.dumps(result, default=json_util.default)
    else:
        response = {}

    return response


@app.route("/get_teacher_options", methods=['GET'])
def getTeacherOptions():
    result = []
    teacher_id = request.args.get('oid')
    teacher = teacherCollection.find_one({'_id': ObjectId(teacher_id)})
    index_oids = teacher['indexes_taught']
    for index_oid in index_oids:
        index = indexCollection.find_one({'_id': ObjectId(index_oid)})
        result.append(dict(index))
        print(result)
    response = make_response(jsonify(result))
    return response


# View attendance for Teacher
@app.route("/view_teacher_attendance", methods=['GET'])
def viewTeacherAttendance():
    course = request.args.get('course')
    group = request.args.get('group')
    attendance_date = str(request.args.get('date'))

    attendance_rec = attendanceCollection.find(
        {"date": attendance_date, "course": course, 'group': group})
    result = []

    # Loop in attendance database to get specific date, module and group
    for entry in attendance_rec:
        student_dict = {'class_index': entry['class_index'], 'student_id': entry['student_id'],
                        'name': entry['name'], 'checkintime': entry['checkintime'], 'attendance': entry['attendance']}
        result.append(student_dict)

    response = make_response(jsonify(result))
    return response


# View attendance for Teacher
@app.route("/take_attendance/manual", methods=['GET'])
def takeAttendanceManual():
    course = request.args.get('course')
    group = request.args.get('group')
    current_date = str(date.today())
    # current_date = '2021-09-15'

    # try to get attendance for today
    attendance_rec = attendanceCollection.find(
        {'date': current_date, 'course': course, 'group': group})
    # copy cursor into list because it will become empty after using once
    att_copy = list(attendance_rec)

    result = []
    # if attendance list exists, get the students and return json
    if att_copy:
        for entry in att_copy:
            student_dict = {'class_index': entry['class_index'],
                            'student_id': entry['student_id'],
                            'name': entry['name'],
                            'checkintime': entry['checkintime'],
                            'attendance': entry['attendance']}
            result.append(student_dict)
    else:
        # get the previous attendance index and add 1 to get new index
        last_att_entry = attendanceCollection.find().sort("attendance_id", -1).limit(1)
        new_att_index = int((list(last_att_entry)[0]['attendance_id'])) + 1

        # find all students under the course and group
        students = studentCollection.find({'course': course, 'group': group})
        class_index = 1
        for student in students:
            new_att_entry = {'attendance_id': new_att_index,
                             'class_index': class_index,
                             'student_id': student['student_id'],
                             'name': student['name'],
                             'date': current_date,
                             'course': course,
                             'group': group,
                             'attendance': 'pending',
                             'checkintime': '-'}
            # add student into attendance list
            attendanceCollection.insert(new_att_entry.copy())
            # add student into the result to be returned to front
            result.append(new_att_entry)
            class_index += 1

    response = make_response(jsonify(result))
    return response


# @app.route("/")
# def index():
#     return '<h1> Hello world database.py </h1>'


@app.route("/login", methods=['GET'])
def getUsers():
    users = []
    for doc in studentCollection.find():
        users.append({
            '_id': str(ObjectId(doc['_id'])),
            'username': doc['username'],
            'password': doc['password'],
            'name': doc['name'],
            'gender': doc['gender'],
            # 'indexes_taken': str(ObjectId(doc['_id'])),
            'image': doc['image'],
        })
    return jsonify(users)

# returns the whole database.newStudent


@app.route("/login/student", methods=['GET'])
def getStudents():
    users = []
    docs_list = list(mongo.db.newStudent.find())
    return json.dumps(docs_list, default=json_util.default)

# returns the whole database.newTeacher


@app.route("/login/teacher", methods=['GET'])
def getTeachers():
    users = []
    docs_list = list(mongo.db.newTeacher.find())
    return json.dumps(docs_list, default=json_util.default)

# /get_data/<id>/collection


# @app.route("/get_data/<id>")
# def check(id):
#     doc = mongo.db.newTeacher.find_one({'_id': ObjectId(id)})
#     return json.dumps(doc, default=json_util.default)


@app.route("/get_data/<id>")
def check(id):
    collection = getCollection(id.split('=')[0])
    oid = id.split('=')[1]
    doc = collection.find_one({'_id': ObjectId(oid)})
    return json.dumps(doc, default=json_util.default)


@app.route('/api/')
def home():
    return {'Hello': 'world'}, 200


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
