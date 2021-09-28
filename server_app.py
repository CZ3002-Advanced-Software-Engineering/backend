# * --------- IMPORTS --------- *
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from bson.json_util import dumps, loads
import os
from flask_pymongo import PyMongo
import cv2
import numpy as np
import re
from teachers import Teachers
from courses import Courses
from students import Students

FILE_PATH = os.path.dirname(os.path.realpath(__file__))


# * ---------- Create App --------- *
app = Flask(__name__)


# * ----------MongoDB connect -------*
app.config["MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/test"
mongo = PyMongo(app)

studentCollection = mongo.db.students
teacherCollection = mongo.db.teachers
courseCollection = mongo.db.courses

# * -----------Create routes and functions here ---------




# To avoid cors erros
CORS(app, support_credentials=True)


# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
