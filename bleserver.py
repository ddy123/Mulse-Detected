from flask import Flask, request, jsonify,send_file
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS
import cv2
import numpy as np
import io
from PIL import Image
import requests
import json

app = Flask(__name__)
CORS(app)

@app.route('/gettest', methods=['GET'])
def gettest():
    return 'OK'

@app.route('/ble_server', methods=['POST'])
def detect_objects():

    print(request.get_data())
    
    return jsonify({"success": True}),200



if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True, host='127.0.0.1', port=5005)
