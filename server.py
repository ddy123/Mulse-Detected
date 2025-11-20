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
    # 解码图像
    #nparr = np.frombuffer(image_data, np.uint8)
    #image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    #cv2.imshow('YOLO', image) 
    #cv2.waitKey()
    print(request.headers.get('X-File-Name'))
    send_to_another_api(request.headers.get('X-File-Name'), 'http://127.0.0.1:5005/ble_server')
    #print(image)
    # 创建内存中的图片文件 
    """ img_io = io.BytesIO(image_data)
    img = Image.open(img_io)
    img.show()  """
    # 直接返回图片给浏览器显示
    #return send_file(img_io, mimetype='image/jpeg')
    #return "ok"
    
    return jsonify({"success": True}),200

def send_to_another_api(data, target_url):
    """将数据发送到另一个 HTTP 接口"""
    try:
        print(f"正在发送数据到: {target_url}")
        
        # 设置请求头
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Flask-Detector/1.0'
        }
        
        # 发送 POST 请求
        response = requests.post(
            target_url,
            data=json.dumps(data),
            headers=headers,
            timeout=30  # 30秒超时
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 检查请求是否成功
        if response.status_code == 200:
            print("数据发送成功")
            return True, response.json()
        else:
            print(f"数据发送失败，状态码: {response.status_code}")
            return False, response.text
            
    except requests.exceptions.RequestException as e:
        print(f"发送请求时出错: {str(e)}")
        return False, str(e)
    except Exception as e:
        print(f"处理响应时出错: {str(e)}")
        return False, str(e)

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True, host='127.0.0.1', port=5001)
