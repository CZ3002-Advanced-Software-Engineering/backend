# * --------- IMPORTS --------- *
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

# * -----------Create routes and functions here ---------
@app.route("/attendance", methods=['GET'])
def read():
    attendance = attendanceListCollection.find()
    for x in attendance:
       print(x)
       print("for")
    return ('results')

# To avoid cors erros
CORS(app, support_credentials=True)

# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
