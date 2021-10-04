# * --------- IMPORTS --------- *
from sys import modules
from typing import List
from bson.objectid import ObjectId
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
from bson.json_util import dumps, loads
from datetime import date
import os
from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure
from pymongo import MongoClient

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
courseCollection = mongo.db.newCourses
attendanceCollection = mongo.db.newAttendance
indexCollection = mongo.db.newIndexes


# * -----------Create routes and functions here ---------

# Get the course teacher is in-charge and return relevant course detail
# Course detail : course, date, class, start time, end time, day
# @app.route("/TeacherAttendance/<id>", methods=['GET'])
# def getTeacherAttendance(id):
#     for x in teacherCollection.find_one({'id': id}):
#         Tcourse = request.args.get('module')
#         print(Tcourse)
#     return('result')

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

    attendance_rec = attendanceCollection.find({"date": attendance_date, "course": course, 'group': group})
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
    attendance_rec = attendanceCollection.find({'date': current_date, 'course': course, 'group': group})
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


# To avoid cors erros
CORS(app, support_credentials=True)

# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
