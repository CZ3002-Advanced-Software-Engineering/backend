from flask import Flask, request, url_for, send_file
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb+srv://robinhood:password..12@frasdata.7ea7m.mongodb.net/frasdata?ssl=true&ssl_cert_reqs=CERT_NONE'
mongo = PyMongo(app)

@app.route('/')
def index():
    return '''
        <form method="POST" action = "/upload" enctype = "multipart/form-data">
            <input type="text" name="studentname">
            <input type="text" name="date">
            <input type="file" name="document">
            <input type="submit">
        </form>

    
    '''


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'document' in request.files:
        document = request.files['document']
        mongo.save_file(document.filename, document)
        mongo.db.absent_docs.insert({'name':request.form.get('studentname'), 'date':request.form.get('date'), request.form.get'document_name': document.filename})
        return 'Done!'

#inorder to get attachment link for download href tag must be created in the frontend section
@app.route('/download/<studentname>/<filename>')
def getfile(filename):
    return mongo.send_file(filename) #as_attachment=True#
    
