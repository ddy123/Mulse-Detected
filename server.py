from flask import Flask, request, jsonify,send_file
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS
import cv2
import numpy as np
import io

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/gettest', methods=['GET'])
def gettest():
    print(request.method+'\n')
    print(request.url+'\n')
    print(request.args.get('name')+'\n')
    return request.args.get('name')

@app.route('/posttest', methods=['POST'])
def posttest():
    return "ok"

@app.route('/detect_objects', methods=['POST'])
def detect_objects():
    print(request.method+'\n')
    print(request.url+'\n')
    image_data = request.get_data()
    #print(image_data)
    """  # 解码图像
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    cv2.imshow('YOLO物体检测 - 气味识别', image)  """
    print(request.headers.get('X-File-Name'))
    # 创建内存中的图片文件 
    img_io = io.BytesIO(image_data)
    # 直接返回图片给浏览器显示
    return send_file(img_io, mimetype='image/jpeg')
    #return "ok"
    #return jsonify({"success": True}),200

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True, host='127.0.0.1', port=5001)
