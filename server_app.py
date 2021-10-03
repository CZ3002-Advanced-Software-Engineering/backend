# * --------- IMPORTS --------- *
from flask import Flask, request, jsonify, flash, session, redirect, url_for
from flask_cors import CORS, cross_origin
from bson.json_util import dumps, loads
from bson import ObjectId
import os
from flask_pymongo import PyMongo
import cv2
import numpy as np
import re
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager 
from flask_jwt_extended import create_access_token
#import face_recognition_total
from teachers import Teachers
import logging
from werkzeug.utils import secure_filename

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('HELLO WORLD')


# * ---------- Create App --------- *
app = Flask(__name__)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# * ----------MongoDB connect -------*
#app.config["MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/database"
#app.config["MONGO_URI"] = "mongodb://localhost:27017/FRAS"
app.config["MONGO_URI"] = "mongodb+srv://robinhood:password..12@frasdata.7ea7m.mongodb.net/frasdata?ssl=true&ssl_cert_reqs=CERT_NONE"
mongo = PyMongo(app)

studentCollection = mongo.db.student
teacherCollection = mongo.db.users
moduleCollection = mongo.db.module

#UPLOAD_FOLDER = 'C:\\Users\\USER\\Desktop\\file_upload\\backend\\uploadedfiles'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


# * -----------Create routes and functions here ---------
@app.route('/teacher_info', methods=['GET'])
def getAllTeacherinfo():
  teachers = []
  for doc in teacherCollection.find():
        teachers.append({
            '_id': str(ObjectId(doc['_id'])),
            'name': doc['name'],
            'email': doc['email'],
            'courses': doc['courses']
        })
  return jsonify(teachers)
  #teacher = teacherCollection.find_one({'_id': ObjectId(id)})
  #teacher = Teachers(teacherCollection)
  #teacher = teacher.getTeacher(id)
  #print(teacher)
  #return jsonify({
      #'name': teacher['name'],
      #'courses': teacher['courses'],
      
  

#@app.route('/takeAttendance/')
#def takeAttendance():
  #face_recognition_total.face_recog()

# login authentication for teachers and students maybe
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data['domain'] == 'teacher':
        users = Teachers(teacherCollection)
    elif data['domain'] == 'student':
        users = Students(studentCollection) 
    email = data['email']
    password = data['password']
    result = ""

    response = users.find_one({'email': email})

    if response:
      if response['password'] == password:

          access_token = create_access_token(identity = {
          'name': response['name'],
              
          'email': response['email']
            })
          result = jsonify({'token':access_token})
      else:
          result = jsonify({"error":"Invalid username and password"})
    else:
        result = jsonify({"result":"No results found"})
    return result 

# upload file for student
@app.route('/upload', methods=['POST'])
def fileUpload():
    if 'file' in request.files:
        file = request.files['file']
        mongo.save_file(file.filename, file)
        return "Done"
    else:
        return "submit a file!"

    

    #mongo.save_file(file.filename, file)
    #mongo.db.userdocs.insert({'doc_name': file.filename})

    #return response
    
# get the file maybe
@app.route('/file/<filename>')
def getfile(filename):
    return mongo.send_file(filename)


@app.route('/view_attendance', methods=['POST', 'GET'])
def viewAttendance():
    if request.method == 'POST':
        data = request.get_json()
        module = data['module']
        index = data['index']
        date = data['date']

        result = attendanceCollection.find_one({'module':module, 'index': index, 'date': date})
        attendanceObj = loads(result)
        return dumps(attendanceObj)  









# To avoid cors erros
CORS(app, support_credentials=True)


# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
