# * --------- IMPORTS --------- *
from sys import modules
from typing import List
from bson.objectid import ObjectId
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
from bson.json_util import dumps, loads
import os
from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure
from pymongo import MongoClient

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

# * ---------- Create App --------- *
app = Flask(__name__)

# * ----------MongoDB connect -------*
app.config["MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/database?ssl=true&ssl_cert_reqs=CERT_NONE"
mongo = PyMongo(app)

# * --------MongodbCollection-------*
studentCollection = mongo.db.student
teacherCollection = mongo.db.teacher
courseCollection = mongo.db.course
attendanceListCollection = mongo.db.attendancelist
modulesCollection = mongo.db.module

# * -----------Create routes and functions here ---------

# Get the course teacher is in-charge and return relevant course detail
# Course detail : course, date, class, start time, end time, day
# @app.route("/TeacherAttendance/<id>", methods=['GET'])
# def getTeacherAttendance(id):
#     for x in teacherCollection.find_one({'id': id}):
#         Tcourse = request.args.get('module')
#         print(Tcourse)
#     return('result')

# View attendance for Teacher
@app.route("/ViewAttendance", methods=['GET'])
def viewTeacherAttendance():
    module = request.args.get('module')
    group = request.args.get('group')

    result = []
    # Loop in attendance database to get specific module and group
    for entry in attendanceListCollection.find({"module": module, 'group': group}):
        student_dict = {'id': entry['id'], 'name': entry['name'], 'checkintime': entry['checkintime'],
                        'attendance': entry['attendance']}
        # print(student_dict)
        result.append(student_dict)

    # print(result)
    response = make_response(jsonify(result))
    return response

# To avoid cors erros
CORS(app, support_credentials=True)

# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
