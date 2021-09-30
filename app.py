from flask import Flask, request
from flask_cors import CORS
from face_rec import FaceRec
from PIL import Image
import base64
import io
import os
import shutil
import time

app = Flask(__name__)
CORS(app)


@app.route('/encode_images', methods=['GET'])
def encode():
    start = time.perf_counter()
    FaceRec('./known-people', './stranger', './encoding').encode_images()
    stop = time.perf_counter()
    print(stop - start)
    return 'Encoding Complete'


@app.route('/face_match', methods=['POST', 'GET'])
def api():
    start = time.perf_counter()
    data = request.get_json()
    resp = 'Nobody'
    directory = './stranger'
    if data:
        if os.path.exists(directory):
            shutil.rmtree(directory)

        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
                time.sleep(1)
                result = data['data']
                b = bytes(result, 'utf-8')
                image = b[b.find(b'/9'):]
                im = Image.open(io.BytesIO(base64.b64decode(image)))
                im.save(directory + '/stranger.jpeg')

                resp = FaceRec('./known-people', './stranger', './encoding').recognize_faces()
            except:
                pass
    stop = time.perf_counter()
    print(stop - start)
    return resp


if __name__ == '__main__':
    app.run()
