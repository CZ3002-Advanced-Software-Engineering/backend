# * --------- IMPORTS --------- *
from sys import modules
from typing import List
from bson.objectid import ObjectId
from flask import Flask, request, jsonify
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
app.config["MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/database"
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
@app.route("/ViewAttendance/<module>/<group>", methods=['GET'])
def viewTeacherAttendance(module, group):
    # Loop in attendance database to get specific module
    for x in attendanceListCollection.find({"module": module}):
        # Check if group in module
        if group in list(x.values()):
            # return list of the student in group
            result = dumps(x)
            print(result)
    # Return result in json
    return (result)

# To avoid cors erros
CORS(app, support_credentials=True)

# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
