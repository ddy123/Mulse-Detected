from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)

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
    print(request.method+'\n')
    print(request.url+'\n')
    print(request.args.get('name')+'\n')
    return request.args.get('name')

@app.route('/detect_objects', methods=['POST'])
def detect_objects():
    print(request.method+'\n')
    print(request.url+'\n')
    print(request.args.get('name')+'\n')
    return request.args.get('name')


if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True, host='127.0.0.1', port=5001)
