import os
import sys
from flask_cors import CORS
from datetime import datetime,timedelta
import time

import traceback
from pathlib import Path

base_dir = os.path.dirname(os.path.abspath(__file__)) + str(Path("/pyaci"))
sys.path.insert(0, base_dir)

import globalvar as gl

#要在其他py起來前執行讀取參數的動作
gl.read_config_ini()
gl.read_env()
#確認process是否開好了(only process can change.)
gl.set_value('PROCESS_READY', False)

from flask import Flask, render_template, jsonify, request, Response, make_response
from markupsafe import escape

import json
from service.deviceService import DeviceService
from apiApp import apiApp
from apiAppDefault import apiAppDefault
from service.properties import Proerties
from flask_socketio import SocketIO,emit



"""
1. app是一個網頁的初始建構
2. CORS可以設定哪些網頁的名稱可以進來，如這邊就是"/*"代表所有都可以
3 & 4. 大架構用blueprints來切割不同的模塊，如下：
       apiAppDefault所有創建出來的路徑都要加上"/"(因url_prefix) ： http://127.0.0.1:8088/apiAppDefault
       apiApp有創建出來的路徑都要加上"/v2"(因url_prefix) : http://127.0.0.1:8088/v2/apiApp
    /flask
    |一 /apiAppDefault.py
    |一 /apiApp.py
    |ㄧ /app.py
"""
# Web setting steps.
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.register_blueprint(apiAppDefault, url_prefix="/")
app.register_blueprint(apiApp, url_prefix="/v2")

#網頁架構中的設定，如：這app有secret key，有生命週期30天的設定
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)

# Websocket protocol: socketio提供全工雙向溝通的方法；而不是像Http protocol頁面刷新（要等http去詢問）才可以接收資訊
# 設定app這個網頁走Websocket protocol.
socketio = SocketIO()
socketio.init_app(app)
service = DeviceService.get_instance()


if __name__ == "__main__":
    print("sys.argv:" + str(sys.argv))
    try:
        gl.set_value('PROCESS_READY', True)
        app.run(host="0.0.0.0", port=Proerties.port)
    except Exception as e:
        print('-------- app.py exception: ', e)
        pass


@socketio.on('stream',namespace='/webSocket/stream')
def sensorWebSocketStream(data):
    sleep_time = 1
    try:
        sleep_time = float(data.get("time"))
    except Exception as e:
        sleep_time = 1
    while True:
        result = service.getSensorStreamData()
        if len(result) != 0:
            emit('response',{'code':'200','data':{'list':result}})
        time.sleep(sleep_time)