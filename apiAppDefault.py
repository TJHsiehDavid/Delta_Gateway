from urllib.parse import parse_qs
import urllib.parse as urlparse
from flask import Blueprint
from service.deviceService import DeviceService
from service.sensorService import SensorService
import json
from markupsafe import escape
from flask import Flask, render_template, jsonify, request, Response, make_response
from pathlib import Path
import traceback
import os
import sys
from flask import send_from_directory

print("python version: " + sys.version)

sdk_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = sdk_dir + str(Path("/pyaci"))
sys.path.insert(0, base_dir)

apiAppDefault = Blueprint('apiAppDefault', __name__)

@apiAppDefault.route("/")
def showDoc():
    # print("Base url with port", request.host_url)
    regex0 = "http://www.biczone.com:8088/v1"
    # myHost0 = "http://127.0.0.1:8088/v2"
    myHost0 = request.host_url+"v2"
    f = open(sdk_dir+"/assets/index.html", encoding="utf-8")
    lines = f.read()
    lines = lines.replace(regex0, myHost0)
    f.close()
    return lines

@apiAppDefault.route("/favicon.ico")
def favicon():
    return send_from_directory( sdk_dir+"/assets/",'favicon.ico', mimetype='image/vnd.microsoft.icon')

# @apiAppDefault.route("/webSocketStream.html")
# def showWebSocketStream():
#     f = open("./templates/test/webSocketStream.html")
#     lines = f.read()
#     f.close()
#     return lines
#
#
# @apiAppDefault.route("/monitorStream.html")
# def showMonitorStream():
#     f = open("./templates/test/monitorStream.html")
#     lines = f.read()
#     f.close()
#     return lines
#
#
# @apiAppDefault.route("/stream.html")
# def showStream():
#     f = open("./templates/test/stream.html")
#     lines = f.read()
#     f.close()
#     return lines
