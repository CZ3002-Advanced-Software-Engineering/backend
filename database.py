# * --------- IMPORTS --------- *
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from bson.json_util import dumps, loads
import os
from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure
from pymongo import MongoClient
# import cv2
# import numpy as np
# import re
# from teachers import Teachers
# from courses import Courses
# from students import Students

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

# * ---------- Create App --------- *
app = Flask(__name__)

# * ----------MongoDB connect -------*
app.config["MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/test"
mongo = PyMongo(app)

# * --------MongodbCollection-------*
studentCollection = mongo.db.student
teacherCollection = mongo.db.teacher
courseCollection = mongo.db.course
attendanceListCollection = mongo.db.attendancelist

# * -------MongodbConnectionTest-----*
client = MongoClient()
try:
   client.admin.command('ismaster')
except ConnectionFailure:
   print("Server not available")

# * -----------Create routes and functions here ---------



@app.route("/attendance", methods=['GET'])
def read():
    #attendance = attendanceListCollection.find({'_id': ObjectId(id)})
    attendance = attendanceListCollection.find_one()

    print(attendance)
    # return data
    return jsonify(attendance)

# To avoid cors erros
CORS(app, support_credentials=True)


# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
