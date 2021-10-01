# * --------- IMPORTS --------- *
from flask import Flask, request, jsonify
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

FILE_PATH = os.path.dirname(os.path.realpath(__file__))


# * ---------- Create App --------- *
app = Flask(__name__)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# * ----------MongoDB connect -------*
#app.config["MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/test/database"
#app.config["MONGO_URI"] = "mongodb://localhost:27017/FRAS"
mongo = PyMongo(app)

studentCollection = mongo.db.student
teacherCollection = mongo.db.users
moduleCollection = mongo.db.module


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


@app.route('/login', methods=['POST'])
def login():
  users = mongo.db.users 
  email = request.get_json()['email']
  password = request.get_json()['password']
  result = ""

  response = users.find_one({'email': email})

  if response:
      if bcrypt.check_password_hash(response['password'], password):
          access_token = create_access_token(identity = {
              'first_name': response['first_name'],
              'last_name': response['last_name'],
              'email': response['email']
            })
          result = jsonify({'token':access_token})
      else:
          result = jsonify({"error":"Invalid username and password"})
  else:
      result = jsonify({"result":"No results found"})
  return result 
  









# To avoid cors erros
CORS(app, support_credentials=True)


# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
