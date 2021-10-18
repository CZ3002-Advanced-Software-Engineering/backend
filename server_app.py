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

#studentCollection = mongo.db.student
#teacherCollection = mongo.db.users
#moduleCollection = mongo.db.module
attendanceCollection = mongo.db.newAttendance
docCollection = mongo.db.users

#UPLOAD_FOLDER = 'C:\\Users\\USER\\Desktop\\file_upload\\backend\\uploadedfiles'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


# * -----------Create routes and functions here ---------
# login authentication for teachers and students maybe


# upload a file with respect to current database, not sure
@app.route('/upload', methods=['POST'])
def upload_file():
   
    if 'document' in request.files:
        document = request.files['document']
        mongo.save_file(document.filename, document)
        
        student_id = request.args.get('student_id')
        attendance_id = request.args.get('attendance_id')
  
        docCollection.insert_one({'student_id': ObjectId(student_id), 'attendance_id': ObjectId(attendance_id), 'document_name': document.filename}) 
        doc_oid = docCollection.find_one({'student_id': ObjectId(student_id), 'document_name': document.filename, 'attendance_id': ObjectId(attendance_id)})['_id']
        
        attendanceCollection.find_one_and_update({'_id': ObjectId(attendance_id), 'students.student': ObjectId(student_id)},
                                                 {'$set': {'students.$.documents': ObjectId(doc_oid)}}, upsert = True)
        
        
        return "Uploaded Successfully!"

  
# direct link to download file by fileid
@app.route('/download/<fileid>')
def getfile(fileid):
    query = {'_id': ObjectId(fileid)}
    cursor = docCollection.find_one(query)
    fileName = cursor['document_name']
    return mongo.send_file(fileName) #as_attachment=True#
    




# To avoid cors erros
CORS(app, support_credentials=True)


# * -------------------- Run Server -------------------- *
if __name__ == '__main__':
    # * --- DEBUG MODE: --- *
    app.run(host='127.0.0.1', port=5000, debug=True)
