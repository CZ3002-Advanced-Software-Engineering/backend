from flask import Flask, request, url_for, send_file
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb+srv://robinhood:password..12@frasdata.7ea7m.mongodb.net/frasdata?ssl=true&ssl_cert_reqs=CERT_NONE'
mongo = PyMongo(app)

usersCollection = mongo.db.users
docCollection = mongo.db.docs


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
        #document_id =mongo.db.users.insert_one({'username':request.form.get('username'), 'date': request.form.get('date'), 'document_name': document.filename}).inserted_id
        usersCollection.insert_one({'username':request.form.get('username'), 'date': request.form.get('date'), 'document_name': document.filename})
        doc_oid = usersCollection.find_one({'username':request.form.get('username'), 'date': request.form.get('date'), 'document_name': document.filename})['_id']
        docCollection.insert_one({'index': ObjectId(doc_oid), 'document_name': document.filename})
        #return dumps(document_id)
        return "Done!"

# direct link to download file by fileid
@app.route('/download/<fileid>')
def getfile(fileid):
    query = {'_id': ObjectId(fileid)}
    cursor = usersCollection.find_one(query)
    fileName = cursor['document_name']

    #filename = docCollection.find_one({'index': ObjectId(doc_oid)})
    return mongo.send_file(fileName) #as_attachment=True#
