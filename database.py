# * --------- IMPORTS --------- *
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from bson.json_util import dumps, loads
import os
from flask_pymongo import PyMongo
import cv2
import numpy as np
import re
from PyMongo import MongoClient

# from teachers import Teachers
# from courses import Courses
# from students import Students

#FILE_PATH = os.path.dirname(os.path.realpath(__file__))
mongodb_host = os.environ.get('MONGO_HOST', 'asecluster.mgx31.mongodb.net')
mongodb_port = int(os.environ.get('MONGO_PORT', '27017'))
client = MongoClient(mongodb_host, mongodb_port)
db = client.database
data = db.attendancelist

# * ---------- Create App --------- *
app = Flask(__name__)


# * ----------MongoDB connect -------*
# app.config['MONGO_DBNAME'] = 'database'
# app.config["MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/test"

#mongo = PyMongo(app)

 #studentCollection = mongo.db.students
# teacherCollection = mongo.db.teachers
# courseCollection = mongo.db.courses

#student = mongo.db.database.student

# * -----------Create routes and functions here ---------
@app.route("take_attendance/manual", methods=['GET'])
def lists():
    data_1 = data.find()
    a1="active"
    return (data==data_1)

# @app.route("/")
@app.route("/name", methods=['POST'])
def name():
    name = request.values.get("Name")
    data.insert({"Name":name})
    return redirect("/list")









# @app.route("/manual", methods = ['GET', 'POST'])

# def read():


#     # cursor = student.find()
#     #  for record in cursor:
#     #      name = record["First Name"]
#     #      print(record)
#     return ('manual.html')


# def insert():
#     name = request.args.get("name")
#     myVal = {"name" : name}
#     x = studentCollection.insert_one(myVal)
#     return render_template("response.html", res = x)


# @app.route("/read")
# def read():
#     cursor = studentCollection.find()
#     for record in cursor:
#         name = record["name"]
#         print(record)
#     return render_template("response.html", res = name)

# @app.route("/insert")
# def insert():
#     name = request.args.get("name")
#     myVal = {"name" : name}
#     x = studentCollection.insert_one(myVal)
#     return render_template("response.html", res = x)

# @app.route("/delete")
# def delete():
#     name = request.args.get("name")
#     myquery = {"name" : name}
#     studentCollection.delete_one(myquery)
#     x = "Record delete"
#     return render_template("response.html", res = x)

# @app.route("/update")
# def update():
#     name = request.args.get("name")
#     myquery = {"name" : name}
#     studentCollection.update_one(myquery)
#     x = "Record updated"
#     return render_template("response.html", res = x)
# */

# To avoid cors erros
CORS(app, support_credentials=True)


# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
