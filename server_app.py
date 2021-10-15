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
app.config["MONGO_URI"] = "mongodb+srv://admin:p%40ssw0rd@asecluster.mgx31.mongodb.net/database?ssl=true&ssl_cert_reqs=CERT_NONE"
#app.config["MONGO_URI"] = "mongodb://localhost:27017/FRAS"
mongo = PyMongo(app)

studentCollection = mongo.db.student
teacherCollection = mongo.db.users
moduleCollection = mongo.db.module
attendanceCollection = mongo.db.newAttendance
docCollection = mongo.db.docs

#UPLOAD_FOLDER = 'C:\\Users\\USER\\Desktop\\file_upload\\backend\\uploadedfiles'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


# * -----------Create routes and functions here ---------
# login authentication for teachers and students maybe
@app.route('/login', methods=['POST'])
def login():
    #data = request.get_json()
    data = request.args.get()
    if data['domain'] == 'teacher':
        users = teacherCollection
    elif data['domain'] == 'student':
        users = studentCollection 
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
          #result = jsonify({'token':access_token})
          result = jsonify({'result' : "Log in Successful"})
      else:
          result = jsonify({"error":"Invalid username and password"})
    else:
        result = jsonify({"result":"No results found"})
    return result 

# upload a file with respect to current database, not sure
@app.route('/upload', methods=['POST'])
def upload_file():
    #name = request.args.get('name')
    #course = request.args.get('course')
    #group = request.args.get('index')
    #status = request.args.get('status')
    #date = request.args.get('date')
    student_id = request.args.get('student_id')
    attendance_id = request.args.get('attendance_id')
  
    if 'document' in request.files:
        document = request.files['document']
        mongo.save_file(document.filename, document)
        docCollection.insert_one({'student_id': ObjectId(student_id), 'attendance_id': Object(attendance_id), 'doc_name': document.filename}) 
        doc_oid = docCollection.find_one({'student_id': ObjectId(student_id), 'doc_name': document.filename, 'attendance_id': ObjectId(attendance_id)})['_id']
        #resp_student['documents'] = doc_oid # or ObjectId(doc_oid)???
        attendanceCollection.find_one_and_update({'_id': ObjectId(attendance_id), 'student': ObjectId(student_id)},
                                                 {'$set': {'documents': ObjectId(doc_oid)}}, upsert = True)
        # update into attendancelist the id of document in mongodb part not sure
        
        return "Uploaded Successfully!"

  
# direct link to download file by fileid
@app.route('/download/<fileid>')
def getfile(fileid):
    query = {'_id': ObjectId(fileid)}
    cursor = docCollection.find_one(query)
    fileName = cursor['doc_name']
    return mongo.send_file(fileName) #as_attachment=True#
    




# To avoid cors erros
CORS(app, support_credentials=True)


# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
