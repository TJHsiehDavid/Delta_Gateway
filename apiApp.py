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
import urllib.request
from shutil import copy2

######### for import add start
from pyaci.interactive_pyaci import Interactive
from service.properties import Proerties
from pyaci.aci.aci_uart import Uart
import pyaci.aci.aci_cmd as cmd
import pyaci.aci.aci_evt as evt
from pyaci.mesh.database import MeshDB  # NOQA: ignore unused import
from pyaci.mesh import types as mt  # NOQA: ignore unused import
import time
######### for import add

import globalvar as gl

print("apiApp python version: " + sys.version)

sdk_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = sdk_dir + str(Path("/pyaci"))
sys.path.insert(0, base_dir)

apiApp = Blueprint('apiApp', __name__)

service = DeviceService.get_instance()
sensorService = SensorService.get_instance(service)

#控燈後是否會寫回狀態(True:會寫入DB,False:不會寫入DB)
testSaveDb = gl.get_value('testSaveDb')

#是否印出log(True:會印,False:不會印)(僅部分程式有使用此變數)
MORE_LOG = gl.get_value('MORE_LOG')

@apiApp.route("/")
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


"""
- 訪問 : http://localhost:8088/version
- 網頁 : 回傳回應到網頁
"""
@apiApp.route("/version")
def v2version():
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": "2.0.0"
    }
    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')

"""
- 訪問 : http://127.0.0.1:8088/bic_postman.html
- 網頁 : 回傳html內容
"""
@apiApp.route("/bic_postman.html")
def showPostman():
    # print("Base url with port", request.host_url)
    # url_arr1 = request.host_url.split('/')
    # url_arr2 = url_arr1[2].split(':')
    # url_arr3 = url_arr2[0].split('.')
    # print("Base url with port split item ip1", url_arr3[0])
    # print("Base url with port split item ip2", url_arr3[1])
    # print("Base url with port split item ip3", url_arr3[2])
    # print("Base url with port split item ip4", url_arr3[3])
    # print("Base url with port split item port", url_arr2[1])

    regex0 = "http://172.16.0.95:8877/v1"
    # myHost0 = "http://127.0.0.1:8088/v2"
    myHost0 = request.host_url+"v2"
    f = open(sdk_dir+"/assets/bic_postman.html", encoding="utf-8")
    lines = f.read()
    lines = lines.replace(regex0, myHost0)
    f.close()
    return lines

@apiApp.route("/postman_collection.json")
def showPostmanJson():
    # print("Base url with port", request.host_url)
    url_arr1 = request.host_url.split('/')
    url_arr2 = url_arr1[2].split(':')
    url_arr3 = url_arr2[0].split('.')
    # print("Base url with port split item ip1", url_arr3[0])
    # print("Base url with port split item ip2", url_arr3[1])
    # print("Base url with port split item ip3", url_arr3[2])
    # print("Base url with port split item ip4", url_arr3[3])
    # print("Base url with port split item port", url_arr2[1])

    regex0 = "http://172.16.0.95:8877/v1"
    regex1 = "\t\t\t\t\t\t\"172\""
    regex2 = "\t\t\t\t\t\t\"16\""
    regex3 = "\t\t\t\t\t\t\"0\""
    regex4 = "\t\t\t\t\t\t\"95\""
    regex5 = "\"8877\""
    regex6 = "\"v1\""
    regex7 = "\"biczone\""
    # myHost0 = "http://127.0.0.1:8088/v2"
    myHost0 = request.host_url+"v2"
    myHost1 = "\t\t\t\t\t\t\""+url_arr3[0]+"\""
    myHost2 = "\t\t\t\t\t\t\""+url_arr3[1]+"\""
    myHost3 = "\t\t\t\t\t\t\""+url_arr3[2]+"\""
    myHost4 = "\t\t\t\t\t\t\""+url_arr3[3]+"\""
    myHost5 = "\""+url_arr2[1]+"\""
    myHost6 = "\"v2\""
    myHost7 = "\"biczone python\""
    f = open(sdk_dir+"/assets/biczone.postman_collection.json", encoding="utf-8")
    lines = f.read()
    lines = lines.replace(regex0, myHost0).replace(regex1,myHost1).replace(regex2,myHost2).replace(regex3,myHost3).replace(regex4,myHost4).replace(regex5,myHost5).replace(regex6,myHost6).replace(regex7,myHost7)
    f.close()
    return Response(lines,mimetype="text/plain",headers={"Content-disposition":"attachment; filename=postman_collection.json"})


@apiApp.route("/mesh/heart0", methods=["post"])
def meshheart0():
    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    content = request.get_json()
    light_id = content['light_id']
    try:
        if MORE_LOG:
            print("getConfigurationClient_heartbeat_publication_get start")
        service.getConfigurationClient_heartbeat_publication_get(light_id)
        if MORE_LOG:
            print("getConfigurationClient_heartbeat_publication_get end")

        result['status'] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/mesh/heart00", methods=["post"])
def meshheart00():
    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    content = request.get_json()
    light_id = content['light_id']
    dst = content['dst']
    try:
        # service.ccPublishSet(light_id)
        if MORE_LOG:
            print("getConfigurationClient_heartbeat_publication_set start")
        #getConfigurationClient_heartbeat_publication_set(dst, count, period)
        service.getConfigurationClient_heartbeat_publication_set2(light_id,dst,64)
        if MORE_LOG:
            print("getConfigurationClient_heartbeat_publication_set end")

        result['status'] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')

@apiApp.route("/mesh/heart1", methods=["post"])
def meshheart():
    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    content = request.get_json()
    light_id = content['light_id']
    try:

        # service.ccPublishSet(light_id)
        if MORE_LOG:
            print("getConfigurationClient_heartbeat_subscription_get start")
        service.getConfigurationClient_heartbeat_subscription_get(light_id)
        if MORE_LOG:
            print("getConfigurationClient_heartbeat_subscription_get end")

        result['status'] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/mesh/heart11", methods=["post"])
def meshheart11():
    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    content = request.get_json()
    light_id = content['light_id']
    src = content['src']
    dst = content['dst']
    try:
        # service.ccPublishSet(light_id)
        if MORE_LOG:
            print("getConfigurationClient_heartbeat_subscription_set start")
        service.getConfigurationClient_heartbeat_subscription_set(light_id,src,dst,64)
        if MORE_LOG:
            print("getConfigurationClient_heartbeat_subscription_set end")

        result['status'] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')




@apiApp.route("/mesh/import", methods=["post"])
def doImport():
    global service
    global sensorService
    content = request.get_json()
    # jsonUrl = content['jsonUrl']
    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        # print("import get json file start :"+jsonUrl)
        # # urllib.request.urlretrieve("http://liby.synology.me:7680/~liby/LTDMS20210624.json", "./pyaci/data/LTDMS.json")
        # urllib.request.urlretrieve(jsonUrl, "./pyaci/data/LTDMS.json")
        # print("import get json file end")

        if MORE_LOG:
            print("import write json file start")
        with open(sdk_dir+"/pyaci/data/LTDMS.json", "w") as LTDMFh:
            LTDMFh.write(json.dumps(content))
        if MORE_LOG:
            print("import write json file end")

        time.sleep(1)
        service.clear_dataDao()
        service.clear()

        if MORE_LOG:
            print("import service.clear done")
        time.sleep(5)
        if MORE_LOG:
            print("import importConfig start ")
        device1 = Interactive(acidev=Uart(port=Proerties.dev_com,
                                  baudrate=Proerties.dev_baudrate,
                                  device_name=Proerties.dev_com.split("/")[-1]),myDEFAULT_LOCAL_UNICAST_ADDRESS_START=(int(content['MeshInfo']["provisionedData"]["provisioners"][0]["provisionerAddress"], 16)))
        if MORE_LOG:
            print("import importConfig provisionerAddress:" + content['MeshInfo']["provisionedData"]["provisioners"][0]["provisionerAddress"] )
        device1.web_import_init( int(content['MeshInfo']["provisionedData"]["provisioners"][0]["provisionerAddress"], 16)  )
        importConfig(device1)
        # device1.close()
        # device1 = None
        if MORE_LOG:
            print("import importConfig end ")

        time.sleep(10)
        # time.sleep(2)

        if MORE_LOG:
            print("import reload_setup start ")
        # device2 = Interactive(Uart(port=Proerties.dev_com,
        #                           baudrate=Proerties.dev_baudrate,
        #                           device_name=Proerties.dev_com.split("/")[-1]))
        # # device2.web_import_init( int(content['MeshInfo']["provisionedData"]["provisioners"][0]["provisionerAddress"], 16)  )
        # device2.reload_setup()
        # device2.close()
        # device2 = None
        device1.reload_setup()
        device1.close()
        device1 = None
        if MORE_LOG:
            print("import reload_setup end ")
        time.sleep(10)
        if MORE_LOG:
            print("import service start ")

        service = DeviceService.get_instance2(myDEFAULT_LOCAL_UNICAST_ADDRESS_START=(int(content['MeshInfo']["provisionedData"]["provisioners"][0]["provisionerAddress"], 16)))
        sensorService = SensorService.get_instance(service)


        if MORE_LOG:
            print("import service start end ")

        result['status'] = "success"
        result['payload'] = content

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]

    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')

@apiApp.route("/mesh/reset")
def resetAll():
    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        service.dongleReset()
        result['status'] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/mesh/scan")
def v1meshScan():
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }

    try:
        is_clear = True if request.args.get('is_clear') == 'true' else False
        result["payload"]['devices'] = service.scanDevice(is_clear)
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    # return jsonify(result)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')



@apiApp.route("/mesh/export")
def v2meshExport():
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }

    try:
        # result["payload"] = {
        #     "MeshInfo": ""
        # }
        result = {
            "status": "failed",
            "code": 501,
            "message": "python server not support Export",
            "payload": ""
        }
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    # return jsonify(result)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/mesh")
def v2mesh():
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }

    try:
        result["payload"] = service.getMeshInfo()

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/config")
def getConfig():
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }

    try:
        result["payload"] = {
            "options":{
                "DEV_COM":gl.get_value("DEV_COM"),
                "DEV_BAUDRATE":gl.get_value("DEV_BAUDRATE"),
                "PORT":gl.get_value("PORT"),
                "SUB_STATUS": gl.get_value("SUB_STATUS"),
                "MORE_LOG": gl.get_value("MORE_LOG"),
                "TTL": gl.get_value("TTL")
            }
        }

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')



@apiApp.route("/config", methods=["post"])
def setConfig():
    global MORE_LOG
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        content = request.get_json()
        if MORE_LOG:
            print("content:" + str(content))

        has_SUB_STATUS = 'SUB_STATUS' in content['options']
        has_MORE_LOG = 'MORE_LOG' in content['options']
        has_TTL = 'TTL' in content['options']

        if has_SUB_STATUS:
            if content["options"]["SUB_STATUS"] :
                SUB_STATUS = True
            else:
                SUB_STATUS = False
            print("new SUB_STATUS:" + str(SUB_STATUS))
            if SUB_STATUS != gl.get_value("SUB_STATUS"):
                service.doChangeSubStatus(SUB_STATUS)
            gl.set_value("SUB_STATUS", SUB_STATUS)
        if has_MORE_LOG:
            if content["options"]["MORE_LOG"] :
                MORE_LOG = True
            else:
                MORE_LOG = False
            print("new MORE_LOG:" + str(MORE_LOG))
            gl.set_value("MORE_LOG", MORE_LOG)
        if has_TTL:
            if str(content["options"]["TTL"]).isdigit():
                TTL = content["options"]["TTL"]
                print("new TTL:" + str(TTL))
                gl.set_value("TTL",TTL)
                service.setTTL(TTL)
            else:
                print("new TTL is not digit:" + str(TTL))

        gl.write_config_ini()

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')



@apiApp.route("/device/uuid/<num1>/ping", methods=['GET'])
def pingUuidDevice(num1):
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        if MORE_LOG:
            print("uuid ping num1:" + str(num1))
        tmpDevice =  service.getDeviceInfoByUuid(num1)
        if len(tmpDevice) > 0:
            tmp_uniAddress = str(tmpDevice[0]["uniAddress"])
            if MORE_LOG:
                print("tmp_uniAddress:" + tmp_uniAddress)
            device = service.setSingleLightOnOffFlash( int( tmp_uniAddress ) , 0x05)
            if device is not None:
                result["message"] = ""
            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device not found'
        else:
            service.flashSingleLight(num1)


    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/device/id/<num1>/ping", methods=['GET'])
def pingIdDevice(num1):
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        if MORE_LOG:
            print("id ping num1:" + str(num1))
        # service.flashSingleLight(num1)
        tmpDevice =  service.getDeviceInfoById(num1)
        if len(tmpDevice) > 0:
            tmp_uniAddress = str(tmpDevice[0]["uniAddress"])
            if MORE_LOG:
                print("tmp_uniAddress:" + tmp_uniAddress)
            device = service.setSingleLightOnOffFlash( int( tmp_uniAddress ) , 0x05)
            if device is not None:
                result["message"] = ""
            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device not found'
        else:
            result["code"] = 400
            result["status"] = "Fail"
            result["message"] = 'device not found'
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')

@apiApp.route("/device/uniAddress/<num1>/ping", methods=['GET'])
def pingUniAddressDevice(num1):
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        if MORE_LOG:
            print("uniAddress ping num1:" + str(num1))
        # service.flashSingleLight(num1)
        device = service.setSingleLightOnOffFlash(int(num1), 0x05)
        if device is not None:
            result["message"] = ''
        else:
            result["code"] = 400
            result["status"] = "Fail"
            result["message"] = 'device not found'
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/device/uniAddress/<num1>/output/<output1>", methods=['GET'])
def setUniAddressDeviceOutput(num1,output1):
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        if MORE_LOG:
            print("uniAddress setUniAddressDeviceOutput num1:" + str(num1) + " output1 " + str(output1) )
        if output1 != "log" and output1 != "linear":
            result["code"] = 400
            result["status"] = "Fail"
            result["message"] = 'parameter output not accept'
        else:
            result_data = service.setSingleLightOutput(int(num1), output1)
            if result_data is not None:
                if result_data != {}:
                    result["message"] = ''
                    result_data["output"] = result_data[int(num1)]
                    del result_data[int(num1)]
                    result["payload"] = result_data
                else:
                    result["code"] = 400
                    result["status"] = "Fail"
                    result["message"] = 'device timeout'
            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device not found'
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')



@apiApp.route("/group/uniAddress/<num1>/output/<output1>", methods=['GET'])
def setUniAddressGroupOutput(num1,output1):
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        if MORE_LOG:
            print("uniAddress setUniAddressGroupOutput num1:" + str(num1) + " output1 " + str(output1) )
        if output1 != "log" and output1 != "linear":
            result["code"] = 400
            result["status"] = "Fail"
            result["message"] = 'parameter output not accept'
        else:
            result_data = service.setGroupOutput(int(num1), output1)
            if result_data is not None:
                if result_data != {}:
                    result["message"] = ''
                    result_data["output"] = result_data[int(num1)]
                    del result_data[int(num1)]
                    result["payload"] = result_data
                else:
                    result["code"] = 400
                    result["status"] = "Fail"
                    result["message"] = 'device timeout'
            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device not found'
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')



@apiApp.route("/device/uniAddress/<num1>/output/", methods=['GET'])
@apiApp.route("/device/uniAddress/<num1>/output", methods=['GET'])
def getUniAddressDeviceOutput(num1):
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        if MORE_LOG:
            print("uniAddress outputUniAddressDevice num1:" + str(num1))
        result_data = service.getSingleLightOutput(int(num1))
        if result_data is not None:
            if result_data != {} :
                result["message"] = ''
                result_data["output"] = result_data[int(num1)]
                del result_data[int(num1)]
                result["payload"] = result_data
            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device timeout'
        else:
            result["code"] = 400
            result["status"] = "Fail"
            result["message"] = 'device not found'
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')



@apiApp.route("/device/realtime/uuid/<num1>", methods=['GET'])
def realtimeUuidDevice(num1):
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        if MORE_LOG:
            print("uuid realtime num1:" + str(num1))
        tmpDevice =  service.getDeviceInfoByUuid(num1)
        if len(tmpDevice) > 0:
            tmp_uniAddress = str(tmpDevice[0]["uniAddress"])
            if MORE_LOG:
                print("tmp_uniAddress:" + tmp_uniAddress)
            deviceData = service.getSingleLight( int(tmp_uniAddress) )
            if deviceData is not None:
                device = service.getDeviceInfoData(deviceData["id"])
                if deviceData["state"]:
                    device.switch_state = 1
                else:
                    device.switch_state = 0
                device.dimming_value = deviceData["lightness"]
                device.color_value = deviceData["temperature"]

                if testSaveDb:
                    service.updateDeviceInfo(device)

                # print("device:"+str(device))
                result["message"] = ""
                result["payload"] = {
                    "devices": [
                        {
                            "id": device.id,
                            "name": device.name,
                            "uniAddress": device.unicast_address,
                            "uuid": device.uuid,
                            "state": {
                                "onOff": device.switch_state,
                                "level": device.dimming_value,
                                "cct": device.color_value
                            }
                        }
                    ]
                }

            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device not found'
        else:
            result["code"] = 400
            result["status"] = "Fail"
            result["message"] = 'device not found'


    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/device/realtime/uniAddress/<num1>", methods=['GET'])
def realtimeUniAddressDevice(num1):
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        if MORE_LOG:
            print("uniAddress realtime num1:" + str(num1))
        deviceData = service.getSingleLight(int(num1))
        if deviceData is not None:
            device = service.getDeviceInfoData(deviceData["id"])
            if deviceData["state"]:
                device.switch_state = 1
            else:
                device.switch_state = 0
            device.dimming_value = deviceData["lightness"]
            device.color_value = deviceData["temperature"]

            if testSaveDb:
                service.updateDeviceInfo(device)

            # print("device:"+str(device))
            if deviceData["timeout"] == True:
                result["message"] = ""
            else:
                result["message"] = "timeout"

            result["payload"] = {
                "devices": [
                    {
                        "id": device.id,
                        "name": device.name,
                        "uniAddress": device.unicast_address,
                        "uuid": device.uuid,
                        "state": {
                            "onOff": device.switch_state,
                            "level": device.dimming_value,
                            "cct": device.color_value
                        }
                    }
                ]
            }

        else:
            result["code"] = 400
            result["status"] = "Fail"
            result["message"] = 'device not found'


    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/device/realtime/id/<num1>", methods=['GET'])
def realtimeIdDevice(num1):
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        if MORE_LOG:
            print("id realtime num1:" + str(num1))
        tmpDevice =  service.getDeviceInfoById(num1)

        if len(tmpDevice) > 0:
            tmp_uniAddress = str(tmpDevice[0]["uniAddress"])
            if MORE_LOG:
                print("tmp_uniAddress:" + tmp_uniAddress)
            deviceData = service.getSingleLight( int(tmp_uniAddress) )
            if deviceData is not None:
                device = service.getDeviceInfoData(deviceData["id"])
                if deviceData["state"]:
                    device.switch_state = 1
                else:
                    device.switch_state = 0
                device.dimming_value = deviceData["lightness"]
                device.color_value = deviceData["temperature"]

                if testSaveDb:
                    service.updateDeviceInfo(device)

                # print("device:"+str(device))
                result["message"] = ""
                result["payload"] = {
                    "devices": [
                        {
                            "id": device.id,
                            "name": device.name,
                            "uniAddress": device.unicast_address,
                            "uuid": device.uuid,
                            "state": {
                                "onOff": device.switch_state,
                                "level": device.dimming_value,
                                "cct": device.color_value
                            }
                        }
                    ]
                }

            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device not found'
        else:
            result["code"] = 400
            result["status"] = "Fail"
            result["message"] = 'device not found'


    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/device/uuid/<num1>", methods=['GET'])
def getDeviceByUuid(num1):
    parsed = urlparse.urlparse(request.url)
    chk_realtime = "realtime" in parse_qs(parsed.query)
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        if MORE_LOG:
            print("/device/uuid/" + str(num1))
        result["payload"]['devices'] = service.getDeviceInfoByUuid(num1)

        if len(result["payload"]['devices']) == 0:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "找不到資料"
            result["payload"] = ""
        else:
            if chk_realtime:
                realtime = parse_qs(parsed.query)['realtime'][0]
                if MORE_LOG:
                    print("realtime:"+realtime)
                if realtime == "onOff" :
                    result2 = service.getSingleLightOnOff( int(result["payload"]['devices'][0]['uniAddress']) )
                elif realtime == "level":
                    result2 = service.getSingleLightLevel( int(result["payload"]['devices'][0]['uniAddress']) )
                elif realtime == "cct":
                    result2 = service.getSingleLightCct( int(result["payload"]['devices'][0]['uniAddress']) )
                else:
                    # 查all,直接套用原func
                    return realtimeUuidDevice(num1)

                # 如果 timeout,就用 db 的回應
                if result2["message"] == 'timeout':
                    result["message"] = 'timeout'
                else:
                    result = result2

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/device/uniAddress/<num1>", methods=['GET'])
def getDeviceByUniAddress(num1):
    parsed = urlparse.urlparse(request.url)
    chk_realtime = "realtime" in parse_qs(parsed.query)
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        if MORE_LOG:
            print("/device/uniAddress/" + str(num1))
        if chk_realtime:
            realtime = parse_qs(parsed.query)['realtime'][0]
            if MORE_LOG:
                print("realtime:"+realtime)
            if realtime == "onOff" :
                result = service.getSingleLightOnOff( int(num1) )
            elif realtime == "level":
                result = service.getSingleLightLevel( int(num1) )
            elif realtime == "cct":
                result = service.getSingleLightCct( int(num1) )
            else:
                # 查all,直接套用原func
                return realtimeUniAddressDevice(num1)

            # 如果 timeout,就抓 db 的回應
            if result["message"] == 'timeout':
                result["payload"]['devices'] = service.getDeviceInfoByUniAddress(num1)

        else:
            result["payload"]['devices'] = service.getDeviceInfoByUniAddress(num1)

        if len(result["payload"]['devices']) == 0:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "找不到資料"
            result["payload"] = ""

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/device/id/<num1>", methods=['GET'])
def getDeviceById(num1):
    parsed = urlparse.urlparse(request.url)
    chk_realtime = "realtime" in parse_qs(parsed.query)
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        result["payload"]['devices'] = service.getDeviceInfoById(num1)
        if len(result["payload"]['devices']) == 0:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "找不到資料"
            result["payload"] = ""
        else:
            if chk_realtime:
                realtime = parse_qs(parsed.query)['realtime'][0]
                print("realtime:"+realtime)
                if realtime == "onOff" :
                    result2 = service.getSingleLightOnOff( int(result["payload"]['devices'][0]['uniAddress']) )
                elif realtime == "level":
                    result2 = service.getSingleLightLevel( int(result["payload"]['devices'][0]['uniAddress']) )
                elif realtime == "cct":
                    result2 = service.getSingleLightCct( int(result["payload"]['devices'][0]['uniAddress']) )
                else:
                    # 查all,直接套用原func
                    return realtimeIdDevice(num1)

                # 如果 timeout,就用 db 的回應
                if result2["message"] == 'timeout':
                    result["message"] = 'timeout'
                else:
                    result = result2

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/device")
def deviceList():
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        result["payload"]['devices'] = service.getDeviceInfoList()
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"

        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')



@apiApp.route("/device", methods=["post"])
def deviceAdd():
    content = request.get_json()
    print("content:" + str(content))
    device_list = content['devices']

    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {
            "devices": []
        }
    }
    try:
        for device in device_list:
            uuid = device['uuid']
            default_name = ""
            if 'defaultName' in device:
                default_name = device['defaultName']
            print("device add uuid:" + str(uuid))
            print("device add default_name:" + str(default_name))

            if result["code"] == 200 :
                node = service.addSingleLight(uuid, default_name)
                # node = service.addSingleLight(uuid, "")
                if node is not None:
                    device_data = service.getDeviceInfoData(int(node.unicast_address))
                    devices = {
                        'id': device_data.id,
                        'uuid': device_data.uuid,
                        'uniAddress': node.unicast_address,
                        'defaultName': device_data.default_name,
                        'meshState': device_data.mesh_state,
                        'sensorClientGroupAddress': device_data.sensor_client_group_address,
                        'rssi': device_data.rssi,
                        'deviceDescription': device_data.device_description
                    }
                    result['payload']['devices'].append(devices)
                    time.sleep(3)
                else:
                    result["status"] = "failed"
                    result["code"] = 500
                    result["error"] = "Time Out"

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')

@apiApp.route("/device", methods=["delete"])
def deviceDelete():
    content = request.get_json()
    print("content:" + str(content))
    device_list = content['devices']
    device_uni_address = []
    for device in device_list:
        uniAddress = device['uniAddress']
        if uniAddress > 0:
            print("delete uniAddress:"+str(uniAddress))
        else:
            id = device['id']
            if id > 0:
                tmpDevice = service.getDeviceInfoById(id)
                if len(tmpDevice) > 0:
                    uniAddress = tmpDevice[0]["uniAddress"]
            if uniAddress > 0:
                print("delete id uniAddress:"+str(uniAddress))
            else:
                uuid = device['uuid']
                tmpDevice = service.getDeviceInfoByUuid(uuid)
                if len(tmpDevice) > 0:
                    uniAddress = tmpDevice[0]["uniAddress"]
                    print("delete uuid uniAddress:"+str(uniAddress))

        device_uni_address.append(uniAddress)

    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        service.deleteSingleLight(device_uni_address)
        # result['payload']['devices'] = content['devices']
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/getSingleLightSensor_descriptorGet", methods=["post"])
def getSingleLightSensor_descriptorGet():
    demo = {
        "uniAddress": 4
    }
    content = request.get_json()
    uniAddress = content['uniAddress']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        values = service.getSingleLightSensor_descriptorGet(uniAddress=uniAddress)
        result["payload"] = {
            "values" : values
        }

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "Fail"
        result["error"] = str(e)
        result["code"] = 500
        result["message"] = 'Exception Error'

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/getSingleLightSensor_cadenceGet", methods=["post"])
def getSingleLightSensor_cadenceGet():
    demo = {
        "uniAddress": 4,
        "propertyID": 77
    }
    content = request.get_json()
    uniAddress = content['uniAddress']
    propertyID = content['propertyID']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        values = service.getSingleLightSensor_cadenceGet(uniAddress=uniAddress,propertyID=propertyID)
        result["payload"] = {
            "values" : values
        }
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "Fail"
        result["error"] = str(e)
        result["code"] = 500
        result["message"] = 'Exception Error'

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/getSingleLightSensor_cadenceSet", methods=["post"])
def getSingleLightSensor_cadenceSet():
    demo = {
        "uniAddress": 4,
        "propertyID": 77,
        "periodDivisor": 1,
        "triggerType": 0,
        "triggerDeltaDown": 1,
        "triggerDeltaUp": 2,
        "minInterval": 3,
        "low": 4,
        "high": 5
    }
    content = request.get_json()
    uniAddress = content['uniAddress']
    propertyID = content['propertyID']
    periodDivisor = content['periodDivisor']
    triggerType = content['triggerType']
    triggerDeltaDown = content['triggerDeltaDown']
    triggerDeltaUp = content['triggerDeltaUp']
    minInterval = content['minInterval']
    low = content['low']
    high = content['high']

    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        values = service.getSingleLightSensor_cadenceSet(uniAddress=uniAddress,propertyID=propertyID,periodDivisor=periodDivisor, triggerType=triggerType, triggerDeltaDown=triggerDeltaDown, triggerDeltaUp=triggerDeltaUp, minInterval=minInterval, low=low, high=high)
        result["payload"] = {
            "values" : values
        }
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "Fail"
        result["error"] = str(e)
        result["code"] = 500
        result["message"] = 'Exception Error'

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/getSingleLightSensor_settingsGet", methods=["post"])
def getSingleLightSensor_settingsGet():
    demo = {
        "uniAddress": 4,
        "propertyID":240
    }
    content = request.get_json()
    uniAddress = content['uniAddress']
    propertyID = content['propertyID']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        values = service.getSingleLightSensor_settingsGet(uniAddress=uniAddress,propertyID=propertyID)
        result["payload"] = {
            "values" : values
        }
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "Fail"
        result["error"] = str(e)
        result["code"] = 500
        result["message"] = 'Exception Error'

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')

@apiApp.route("/getSingleLightSensor_settingGet", methods=["post"])
def getSingleLightSensor_settingGet():
    demo = {
        "uniAddress": 4,
        "propertyID":240,
        "settingPropertyID":18
    }
    content = request.get_json()
    uniAddress = content['uniAddress']
    propertyID = content['propertyID']
    settingPropertyID = content['settingPropertyID']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        values = service.getSingleLightSensor_settingGet(uniAddress=uniAddress,propertyID=propertyID,settingPropertyID=settingPropertyID)
        result["payload"] = {
            "values" : values
        }
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "Fail"
        result["error"] = str(e)
        result["code"] = 500
        result["message"] = 'Exception Error'

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/getSingleLightSensor_settingSet", methods=["post"])
def getSingleLightSensor_settingSet():
    demo = {
        "uniAddress": 4,
        "propertyID":240,
        "settingPropertyID":18,
        "settingValue": "0123456789abcdef0123456789abcdef"
    }
    content = request.get_json()
    uniAddress = content['uniAddress']
    propertyID = content['propertyID']
    settingPropertyID = content['settingPropertyID']
    settingValue = content['settingValue']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        values = service.getSingleLightSensor_settingSet(uniAddress=uniAddress,propertyID=propertyID,settingPropertyID=settingPropertyID,settingValue=settingValue)
        result["payload"] = {
            "values" : values
        }
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "Fail"
        result["error"] = str(e)
        result["code"] = 500
        result["message"] = 'Exception Error'

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/getSingleLightSensor_Publish", methods=["post"])
def getSingleLightSensor_Publish():
    demo = {
        "uniAddress": 4,
        "enable":1,
        "publishType":1,
        "publishUniAddress": -1
    }
    # publishUniAddress = -1 表示定給 python server
    demo2 = {
        "uniAddress": 20,
        "enable":1,
        "publishType":3,
        "publishUniAddress": 49168
    }

    # TYPE_SINGLE_LIGHT = 1
    # TYPE_GROUP = 3
    content = request.get_json()
    uniAddress = content['uniAddress']
    enable = content['enable']
    publishType = content['publishType']
    publishUniAddress = content['publishUniAddress']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        publish_result = service.getSingleLightSensor_Publish(uniAddress=uniAddress,enable=enable,publishType=publishType,publishUniAddress=publishUniAddress)
        result["payload"] = {
            "publish_result" : publish_result
        }
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "Fail"
        result["error"] = str(e)
        result["code"] = 500
        result["message"] = 'Exception Error'

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/lsbu", methods=["GET"])
def energyLogUpdate():
    content = request.get_json()
    id = content['device']['uniAddress']
    transition_time = 'transitionTime' in content['device']
    repeat = 'repeat' in content['device']

    hours = 'hours' in content['device']['state']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }

    # transition time checked
    if transition_time:
        transition_time_value = content['device']['transitionTime']
    else:
        transition_time_value = 0
    # transition time checked
    if repeat:
        repeat_value = content['device']['repeat']
    else:
        repeat_value = 3


    if id > 0:
        print("device patch:"+str(id))
    else:
        print("device ID is wrong")

    if hours:
        try:
            hours_value = content['device']['state']['hours']

            device = service.setLsbuEnergyTime(id, 0xd5, int(hours_value), transition_time_value, repeat_value)
            if device is not None:
                #device = service.getDeviceInfoData(deviceData["unicast_address"])
                if device['timeout'] is True:
                    result["message"] = 'timeout'
                else:
                    result["message"] = ''

                print(device['id'])
                print(device['name'])

                result["payload"] = {
                    "devices": [
                        {
                            "id": device['id'],
                            "name": device['name'],
                            "uniAddress": device['uniAddress'],
                            'deviceDescription': device['deviceDescription'],
                            'transitionTime': device['transitionTime'],
                            'repeat': device['repeat'],
                            'state': {
                                'data': str(device['state']['data'])
                            }
                        }
                    ]
                }

        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "Fail"
            result["error"] = str(e)
            result["code"] = 500
            result["message"] = 'Exception Error'
    else:
        result["code"] = 400
        result["status"] = "Fail"
        result["message"] = 'device not found'

    status_code = result["code"]
    if status_code == 200:
        return Response(json.dumps(result), mimetype='text/plain')
    else:
        return Response(json.dumps(result), status=status_code, mimetype='text/plain')

@apiApp.route("/device", methods=["patch"])
def deviceUpdate():
    content = request.get_json()
    id = content['device']['uniAddress']
    transition_time = 'transitionTime' in content['device']
    repeat = 'repeat' in content['device']
    ack = 'ack' in content['device']

    on_off = 'onOff' in content['device']['state']
    level = 'level' in content['device']['state']
    cct = 'cct' in content['device']['state']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }

    if id > 0:
        print("device patch:"+str(id))
    else:
        id = content['device']['id']
        tmpDevice = service.getDeviceInfoById(id)
        if len(tmpDevice) > 0:
            id = tmpDevice[0]["uniAddress"]

    #transition time checked
    if transition_time:
        transition_time_value = content['device']['transitionTime']
    else:
        transition_time_value = 0
    # transition time checked
    if repeat:
        repeat_value = content['device']['repeat']
    else:
        repeat_value = 3
    #ack checked
    if ack:
        ack = content['device']['ack']
    else:
        ack = 0

    if on_off:
        try:
            on_off_value = content["device"]["state"]["onOff"]
            device = service.setSingleLightOnOff(int(id), on_off_value, int(transition_time_value), int(repeat_value), ack)
            if device is not None:
                result["payload"] = {
                    "devices": [
                        {
                            "id": device.id,
                            "deviceDescription": device.device_description,
                            "transitionTime": transition_time_value,
                            "repeat": repeat_value,
                            "ack": bool(ack),
                            "state": {
                                "onOff": device.switch_state,
                                "level": device.dimming_value,
                                "cct": device.color_value
                            }
                        }
                    ]
                }
                result["message"] = ''
            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device not found'
        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "Fail"
            result["error"] = str(e)
            result["code"] = 500
            result["message"] = 'Exception Error'

    if level:
        try:
            level1 = content["device"]["state"]["level"]
            # per_step = int(32767 / 50)
            # lightValue = int(level1 / per_step) + 50

            device = service.setSingleLightLightness(int(id), level1, int(transition_time_value), int(repeat_value), ack)
            if device is not None:
                result["payload"] = {
                    "devices": [
                        {
                            "id": device.id,
                            "deviceDescription": device.device_description,
                            "transitionTime": transition_time_value,
                            "repeat": repeat_value,
                            "ack": bool(ack),
                            "state": {
                                "onOff": device.switch_state,
                                "level": device.dimming_value,
                                "cct": device.color_value
                            }
                        }
                    ]
                }
                result["message"] = ''
            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device not found'
        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)
            result["code"] = 500
            result["message"] = 'Exception Error'

    if cct:
        try:
            level2 = content["device"]["state"]["cct"]
            # per_step = int(32767 / 50)
            # lightValue = int(level2 / per_step) + 50

            device = service.setSingleLightTemperature(int(id), level2, int(transition_time_value), int(repeat_value), ack)
            if device is not None:
                result["payload"] = {
                    "devices": [
                        {
                            "id": device.id,
                            "deviceDescription": device.device_description,
                            "transitionTime": transition_time_value,
                            "repeat": repeat_value,
                            "ack": bool(ack),
                            "state": {
                                "onOff": device.switch_state,
                                "level": device.dimming_value,
                                "cct": device.color_value
                            }
                        }
                    ]
                }
                result["message"] = ''
            else:
                result["code"] = 400
                result["status"] = "Fail"
                result["message"] = 'device not found'
        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)
            result["code"] = 500
            result["message"] = 'Exception Error'



    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')



@apiApp.route("/group")
def groupListAndGet():
    parsed = urlparse.urlparse(request.url)
    groupQuery = "id" in parse_qs(parsed.query)
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    if groupQuery:
        group_id = parse_qs(parsed.query)['id'][0]
        try:
            group_data = service.getGroupInfoById(group_id)
            group = service.getGroup(int(group_data.unicast_address))
            devices = [device for device in group['device']
                       if device['inUse'] == True]
            for device in devices:
                device_address = device['id']
                device_info = service.getDeviceInfoData(device_address)
                device['id'] = device_info.id
                device['uniAddress'] = device_address
                device["uuid"] = device_info.uuid
                device["state"] = {
                    "onOff": device_info.switch_state,
                    "level": device_info.dimming_value,
                    "cct": device_info.color_value
                }
                del device['inUse']

            del group['device']
            group['devices'] = devices

            group_address = group['id']
            group['uniAddress'] = group_address
            group['id'] = group_data.id
            del group['image']
            result["payload"]['groups'] = []
            result["payload"]['groups'].append(group)

            result["message"] = ""
            result["status"] = "success"

        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)
            result["code"] = 500
    else:
        try:
            result["payload"]['groups'] = service.getGroupList()
            for group in result["payload"]['groups']:
                print("group:" + str(group))
                group_address = group['id']
                del group['image']
                group['uniAddress'] = group_address
                group_data = service.getGroupInfoByAddress(group_address)
                group['id'] = None if group_data is None else group_data.id

            result["message"] = ""
        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)
            result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/group", methods=["post"])
def groupAdd():
    content = request.get_json()
    name = content['name']
    newDevices = content['newDevices']

    result = {
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        group_address_list = []
        devices = []
        for newDevice in newDevices:
            group_address_list.append(newDevice['uniAddress'])
            device_data = service.getDeviceInfoData(newDevice['uniAddress'])
            device = {
                'id': device_data.id,
                'name': device_data.name,
                'uniAddress': device_data.unicast_address
            }
            devices.append(device)

        group_id = service.addGroup(name, group_address_list)
        groups = []
        group_info_data = service.getGroupInfoData(group_id)
        group = {
            'devices': devices,
            "id": group_info_data.id,
            "uniAddress": group_info_data.unicast_address
        }
        groups.append(group)
        result['payload']['groups'] = groups
        result['status'] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/group", methods=["patch"])
def groupUpdate():

    content = request.get_json()
    state = ''
    if "group" in content:
        state = 'state' in content['group']
        transition_time = 'transitionTime' in content['group']
        repeat = 'repeat' in content['group']
        ack = 'ack' in content['group']
    on_off = False
    level = False
    cct = False
    if state:
        on_off = 'onOff' in content['group']['state']
        level = 'level' in content['group']['state']
        cct = 'cct' in content['group']['state']
    result = {
        "code": 200,
        "message": "",
        "payload": {}
    }

    # transition time checked
    if transition_time:
        transition_time_value = content['group']['transitionTime']
    else:
        transition_time_value = 0
    # transition time checked
    if repeat:
        repeat_value = content['group']['repeat']
    else:
        repeat_value = 3
    # ack checked
    if ack:
        ack = content['group']['ack']
    else:
        ack = 0

    if on_off:
        try:
            group_id = content['group']['id']
            uniAddress = content['group']['uniAddress']
            if uniAddress > 0:
                group_id = 0
            else:
                group_data = service.getGroupInfoById(group_id)
                if group_data is not None:
                    uniAddress = int(group_data.unicast_address)

            groups = []
            on_off_value = content['group']['state']['onOff']
            result['payload']['groups'] = groups
            group_info_data = service.setGroupOnOff(int(uniAddress), on_off_value, int(transition_time_value), int(repeat_value), ack)
            now_on_off_value = 0
            if group_info_data.switch_state:
                now_on_off_value = 1
            group = {
                "id": group_info_data.id,
                "uniAddress": group_info_data.unicast_address,
                "transitionTime": transition_time_value,
                "repeat": repeat_value,
                "ack": bool(ack),
                "state": {
                    "onOff": now_on_off_value,
                    "level": group_info_data.dimming_value,
                    "cct": group_info_data.color_value
                }
            }
            groups.append(group)
            result['payload'] = {
                "groups": groups
            }
            result['message'] = ""
            result['status'] = "success"

        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)
            result["code"] = 500

    elif level:
        try:
            group_id = content['group']['id']
            uniAddress = content['group']['uniAddress']
            if uniAddress > 0:
                group_id = 0
            else:
                group_data = service.getGroupInfoById(group_id)
                if group_data is not None:
                    uniAddress = int(group_data.unicast_address)

            groups = []
            level_value = content['group']['state']['level']

            group_info_data = service.setGroupLightness(int(uniAddress), level_value, int(transition_time_value), int(repeat_value), ack)
            now_on_off_value = 0
            if group_info_data.switch_state:
                now_on_off_value = 1
            group = {
                "id": group_info_data.id,
                "uniAddress": group_info_data.unicast_address,
                "transitionTime": transition_time_value,
                "repeat": repeat_value,
                "ack": bool(ack),
                "state": {
                    "onOff": now_on_off_value,
                    "level": group_info_data.dimming_value,
                    "cct": group_info_data.color_value
                }
            }
            groups.append(group)
            result['payload'] = {
                "groups": groups
            }
            result['message'] = ""
            result['status'] = "success"

        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)
            result["code"] = 500
    elif cct:
        try:
            group_id = content['group']['id']
            uniAddress = content['group']['uniAddress']
            if uniAddress > 0:
                group_id = 0
            else:
                group_data = service.getGroupInfoById(group_id)
                if group_data is not None:
                    uniAddress = int(group_data.unicast_address)

            groups = []
            cct_value = content['group']['state']['cct']

            group_info_data = service.setGroupTemperature(int(uniAddress), cct_value, int(transition_time_value), int(repeat_value), ack)
            now_on_off_value = 0
            if group_info_data.switch_state:
                now_on_off_value = 1
            group = {
                "id": group_info_data.id,
                "uniAddress": group_info_data.unicast_address,
                "transitionTime": transition_time_value,
                "repeat": repeat_value,
                "ack": bool(ack),
                "state": {
                    "onOff": now_on_off_value,
                    "level": group_info_data.dimming_value,
                    "cct": group_info_data.color_value
                }
            }
            groups.append(group)
            result['payload'] = {
                "groups": group
            }
            result['message'] = ""
            result['status'] = "success"

        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)
            result["code"] = 500
    else:
        try:
            group_id = content['id']
            group_name = content['name']
            newDevices = content['newDevices']
            delDevices = content['delDevices']

            group_info_data = service.getGroupInfoDataByid(group_id)
            groupData = service.getGroup(int(group_info_data.unicast_address))['device']


            add_device_address_list = []
            for newDevice in newDevices:
                add_device_address_list.append(newDevice['uniAddress'])

            del_device_address_list = []
            for delDevice in delDevices:
                del_device_address_list.append(delDevice['uniAddress'])

            devices = [int(x['id']) for x in groupData if x["inUse"] == True]
            for add_device_address in add_device_address_list:
                if not add_device_address in devices:
                    devices.append(add_device_address)
                    device_data = service.getDeviceInfoData(add_device_address)
                    device_obj = {
                        'id': device_data.id,
                        'name': device_data.name,
                        'uniAddress': device_data.unicast_address
                    }

            for del_device_address in del_device_address_list:
                if del_device_address in devices:
                    devices.remove(del_device_address)
            useDevices = [str(x) for x in devices]
            service.updateGroup(int(group_info_data.unicast_address), group_name, useDevices)

            # 重抓資料
            group_data = service.getGroupInfoById(group_id)
            group = service.getGroup(int(group_data.unicast_address))
            devices = [device for device in group['device']
                       if device['inUse'] == True]
            for device in devices:
                device_address = device['id']
                device_info = service.getDeviceInfoData(device_address)
                device['id'] = device_info.id
                device['uniAddress'] = device_address
                del device['inUse']

            result['payload'] = {
                "groups": [{
                    "id": group_id,
                    "uniAddress": group_info_data.unicast_address,
                    "devices": devices
                }]
            }
            result['message'] = ""
            result['status'] = "success"
        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/group", methods=["delete"])
def groupDelete():
    content = request.get_json()
    group_id = content['group']['id']
    uniAddress = content['group']['uniAddress']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        if uniAddress > 0:
            print("deleteGroup:"+str(uniAddress))
        else:
            group_data = service.getGroupInfoById(group_id)
            if group_data is not None:
                uniAddress = int(group_data.unicast_address)

        service.deleteGroup(int(uniAddress))
        result['payload'] = ""
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/scene")
def sceneList():
    result = {
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        scene_list = service.getSceneList()
        result['payload']['scenes'] = scene_list
        result['status'] = 'success'

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/scene", methods=["post"])
def sceneAdd():
    content = request.get_json()
    name = content['scene']['name']
    aTime = content['scene']['time']
    aLevel = 0
    group_list = []
    result = {
        "code": 200,
        "message": "",
        "payload": {}
    }

    for a_data in content['scene']['group']:
        group_scene_data = {}
        group_scene_data["id"] = a_data['group_id']
        group_scene_data["lightness"] = a_data['state']['level1']
        group_scene_data["temperature"] = a_data['state']['level2']
        group_scene_data["state"] = True if a_data['state']['onOff'] == 1 else False
        group_list.append(group_scene_data)
    try:
        scene_id = service.addScene(name, aTime, aLevel, group_list, None)
        scene_resp = {
            "scene_id": scene_id,
            "name": name
        }
        result['payload']['scene'] = scene_resp
        result['status'] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/scene", methods=["delete"])
def sceneDelete():
    content = request.get_json()
    id = content['scene']['scene_id']
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        service.deleteScene(id)
        result['payload']['scene'] = id
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route('/scene/id/<num1>/recall', methods=['GET'])
def sceneOn(num1):
    parsed = urlparse.urlparse(request.url)
    sceneRepeatQuery = "repeat" in parse_qs(parsed.query)

    print("num1:" + str(num1))
    scene_id = num1
    result = {
        "status": "success",
        "code": 200,
        "message": "",
        "payload": {}
    }

    repeat_value = parse_qs(parsed.query)['repeat'][0]

    try:
        service.controllScene(int(scene_id), int(repeat_value))
        result['payload'] = ""
        result['status'] = 'success'

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/schedule")
def scheduleList():
    parsed = urlparse.urlparse(request.url)
    scheduleQuery = "id" in parse_qs(parsed.query)
    result = {
        "status": "",
        "code": 200,
        "message": "",
        "payload": {}
    }
    if scheduleQuery:
        schedule_id = parse_qs(parsed.query)['id'][0]
        try:
            schedule = service.getSceneSchedule(int(schedule_id))
            if schedule is None:
                result["status"] = "failed"
                result["code"] = 400
                result["message"] = "schedule data not found"
                return jsonify(result)

            result['payload']["schedules"] = []
            result['payload']["schedules"].append(schedule)
            result["message"] = ""
            result["status"] = "success"

        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)
            result["code"] = 500
    else:
        try:
            schedule_list = service.getScheduleList()
            result['payload']['schedules'] = schedule_list
            result["message"] = ""
            result["status"] = "success"
        except Exception as e:
            print(e)
            traceback.print_exc()
            result["status"] = "failed"
            result["error"] = str(e)
            result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/schedule", methods=["post"])
def scheduleAdd():
    content = request.get_json()['schedule']
    name = content['name']
    scene_num = int(content['sceneNum'])
    start_time = content['startTime']
    repeatWeekly = content['repeatWeekly']
    weeks = ''

    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        if name is None:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "schedule name empty"
            return jsonify(result)

        if scene_num == 0:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "scene data not found"
            return jsonify(result)

        if len(repeatWeekly) != 7:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "repeat weekly error"
            return jsonify(result)

        if start_time is None:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "start time error"
            return jsonify(result)

        tmp_start_time = start_time.split(":")
        if len(tmp_start_time) != 2:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "start time error"
            return jsonify(result)

        print("tmp_start_time:" + str(tmp_start_time))
        hours = int(tmp_start_time[0])
        mins = int(tmp_start_time[1])

        if hours < 0 or hours > 23:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "start time error"
            return jsonify(result)

        if mins < 0 or mins > 59:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "start time error"
            return jsonify(result)

        if repeatWeekly is None:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "repeat weekly error"
            return jsonify(result)

        for i in range(len(repeatWeekly)):
            if int(repeatWeekly[i]) == 1:
                a_weeks = str(7 - i) + ','
                weeks = a_weeks + weeks
        weeks = weeks[:-1]

        # schedule_id = service.addSchedule(name, scene_num, weeks, hours, mins)
        schedule_id = service.addScheduleNew(name, scene_num, weeks, hours, mins,0)
        if schedule_id == 0:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "scene's lights don't found unused schedule-id"
        else:
            result["status"] = "success"

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/schedule", methods=["patch"])
def scheduleUpdate():
    content = request.get_json()['schedule']
    schedule_id = int(content['id'])
    sceneNum = int(content['sceneNum'])
    name = content['name']
    start_time = content['startTime']
    repeatWeekly = content['repeatWeekly']
    weeks = ''

    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        if schedule_id == 0:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "schedule not found"
            return jsonify(result)

        if start_time is None:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "start time error"
            return jsonify(result)

        tmp_start_time = start_time.split(":")
        if len(tmp_start_time) != 2:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "start time error"
            return jsonify(result)

        print("tmp_start_time:" + str(tmp_start_time))
        hours = int(tmp_start_time[0])
        mins = int(tmp_start_time[1])

        if hours < 0 or hours > 23:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "start time error"
            return jsonify(result)

        if mins < 0 or mins > 59:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "start time error"
            return jsonify(result)

        if repeatWeekly is None:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "repeat weekly error"
            return jsonify(result)

        for i in range(len(repeatWeekly)):
            if int(repeatWeekly[i]) == 1:
                a_weeks = str(7 - i) + ','
                weeks = a_weeks + weeks
        weeks = weeks[:-1]

        ok = service.updateScheduleNew(schedule_id,sceneNum, name, weeks, hours, mins)
        if ok == 0:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "scene's lights don't found unused schedule-id"
        else:
            result["status"] = "success"

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/schedule", methods=["delete"])
def scheduleDelete():
    schedule_id = request.get_json()['id']
    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:

        if schedule_id == 0:
            result["status"] = "failed"
            result["code"] = 400
            result["message"] = "schedule not found"
            return jsonify(result)

        service.deleteScheduleNew(int(schedule_id))
        result["status"] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)
        result["code"] = 500

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/time", methods=["patch"])
def timeSync():
    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        service.updateTime()

        result["status"] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/time/update", methods=["post"])
def timeUpdate():
    result = {
        "code": 200,
        "message": "",
        "payload": ""
    }
    try:
        service.updateTime()

        result["status"] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/beacon/setup", methods=["post"])
def beaconSetup():
    content = request.get_json()['beacon']
    v1 = int(content["v1"], 16)
    uuid = content["uuid"]
    major_range = content["major_range"]
    minor_range = content["minor_range"]
    add_light_id_ary = []
    remove_light_id_ary = []

    if content.get("add") is not None and content["add"].get("devices") is not None:
        add_light_id_ary = [id for id in content["add"]["devices"]]

    if content.get("remove") is not None and content["remove"].get("devices") is not None:
        remove_light_id_ary = [id for id in content["remove"]["devices"]]

    result = {
        "code": 200,
        "message": "",
        "payload": {
            "sensor": {
                "device_id": []
            }
        }}

    try:
        sensorList = sensorService.getSensorList()
        if (len(sensorList) == 0):
            group_id = sensorService.addSensorGroup('default_group', add_light_id_ary)
            sensorService.addSensor([group_id], v1, uuid, major_range, minor_range)
            result['payload']['sensor']['device_id'] = add_light_id_ary

        else:
            sensor_id = sensorList[0]['id']
            sensorInfo = sensorService.getSensor(sensor_id)

            group_id = int(sensorInfo['groups'][0]['address'])
            groupInfo = sensorService.getSensorGroup(group_id)

            devices = [str(device['id']) for device in groupInfo['device'] if device['inUse'] == True]

            for add_id in add_light_id_ary:
                str_add_id = str(add_id)
                if str_add_id not in devices:
                    devices.append(str_add_id)
            for remove_id in remove_light_id_ary:
                str_remove_id = str(remove_id)
                if str_remove_id in devices:
                    devices.remove(str_remove_id)

            sensorService.updateSensorGroup(group_id, 'default_group', devices)
            sensorService.updateSensor(sensor_id, [group_id], v1, uuid, major_range, minor_range)
            result['payload']['sensor']['device_id'] = devices

        result['status'] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200:
        return Response(json.dumps(result), mimetype='text/plain')
    else:
        return Response(json.dumps(result), status=status_code, mimetype='text/plain')


@apiApp.route("/beacon/info")
def beaconGet():
    result = {
        "code": 200,
        "message": "",
        "payload": {
            "sensor": {}
        }
    }
    try:
        sensorList = sensorService.getSensorList()
        if (len(sensorList) == 0):
            raise Exception("no find sensor")
        else:
            sensor_id = sensorList[0]['id']
            sensorInfo = sensorService.getSensor(sensor_id)
            del sensorInfo['id']
        result["payload"]["sensor"] = sensorInfo
        result["status"] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/beacon/start", methods=["post"])
def runSensor():
    cadence = request.get_json()['beacon']['cadence']
    result = {
        "code": 200,
        "message": "",
    }
    try:
        sensor_list = sensorService.getSensorList()
        if len(sensor_list) == 0:
            result['message'] = "beacon setting don't exist"
            result['status'] = "success"
        else:
            sensor_id = sensor_list[0]['id']
            sensorService.runSensor(sensor_id, cadence)
            result['status'] = "success"
            result['payload'] = {
                "beacon": {
                    "cadence": cadence
                }
            }
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/beacon/stop", methods=["post"])
def stopSensor():
    result = {
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        sensorService.stopSensor()
        result['status'] = "success"

    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/beacon/stream")
def sensorStream():
    return Response(sensorService.getSensorStream(), mimetype="text/event-stream")


@apiApp.route("/beacon/lights")
def sensorLightList():
    result = {
        "code": 200,
        "message": "",
        "payload": {}
    }
    try:
        sensorList = sensorService.getSensorList()
        if (len(sensorList) == 0):
            raise Exception("no find sensor")
        else:
            sensor_id = sensorList[0]['id']
            sensorInfo = sensorService.getSensor(sensor_id)

            group_id = int(sensorInfo['groups'][0]['address'])
            groupInfo = sensorService.getSensorGroup(group_id)
            del groupInfo['id']
            del groupInfo['image']
            groupInfo = [x for x in groupInfo['device'] if x['inUse'] == True]
            result['payload'] = {
                "beacon": groupInfo
            }
        result["status"] = "success"
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    status_code = result["code"]
    if status_code == 200 :
        return Response(json.dumps(result),mimetype='text/plain')
    else :
        return Response(json.dumps(result),status=status_code,mimetype='text/plain')


@apiApp.route("/deviceMonitor/run", methods=["post"])
def deviceMonitorRun():
    resp = make_response("")
    result = {"status": "success"}
    try:
        service.startDeviceMonitor()
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    resp.data = json.dumps(result)
    return resp


@apiApp.route("/deviceMonitor/stop", methods=["post"])
def deviceMonitorStop():
    resp = make_response("")
    result = {"status": "success"}

    try:
        service.stopDeviceMonitor()
    except Exception as e:
        print(e)
        traceback.print_exc()
        result["status"] = "failed"
        result["error"] = str(e)

    resp.data = json.dumps(result)
    return resp


@apiApp.route("/deviceMonitor/stream")
def deviceMonitorStream():
    try:
        return Response(service.getDeviceMonitorStreamList(), mimetype="text/event-stream")
    except Exception as e:
        pass

    return ""


@apiApp.route("/test/<path:subpath>")
def show_subpath_test(subpath):
    return render_template("/test/%s" % escape(subpath))




##################################################
# for import
##################################################

def updateConfig(name, value):
    """INTERNAL FUNCTION"""
    content = None
    with open(sdk_dir+"/pyaci/data/config.json", "r+") as confFh:
        content = confFh.read()
    confJson = json.loads(content) if len(content) > 0 else None
    # 无文件或无deviceInfo，初始化config.json
    if confJson == None or "deviceInfo" not in confJson:
        confJson = {
            "deviceInfo": {"unicastAddress": 0x7fff, "subscription": None}
        }
    if name == 'subscription':
        if name not in confJson["deviceInfo"]:
            confJson["deviceInfo"][name] = [value]
        elif value == []:
            confJson["deviceInfo"][name] = []
        elif value not in confJson["deviceInfo"][name]:
            confJson["deviceInfo"][name].append(value)
    else:
        confJson["deviceInfo"][name] = value
    with open(sdk_dir+"/pyaci/data/config.json", "w") as confFh:
        confFh.write(json.dumps(confJson))


def getDeviceConfig(name):
    """INTERNAL FUNCTION"""
    with open(sdk_dir+"/pyaci/data/config.json", "r") as confFh:
        # content = confFh.read()
        content = confFh.read()
        if len(content) <= 0:
            return False
        else:
            confJson = json.loads(content)
            if "deviceInfo" in confJson and name in confJson["deviceInfo"]:
                return confJson["deviceInfo"][name]
            else:
                return False

def importConfig(dev, configFile=sdk_dir+"/pyaci/data/LTDMS.json", removeFile=True):
    removeFile = False
    copy2(sdk_dir+"/pyaci/database/example_database.json.backup", sdk_dir+"/pyaci/database/example_database.json")
    db = MeshDB(path=sdk_dir+"/pyaci/database/example_database.json")

    # 需要先reset()
    if not os.path.isfile(configFile):
        print(sdk_dir+"/pyaci/data/LTDMS.json NOT EXIST!")
        return False
    conf = json.loads(open(configFile, "r+", encoding='utf-8-sig').read())["MeshInfo"]
    uni = getDeviceConfig("unicastAddress")
    localUnicastAddr = int(conf["provisionedData"]["provisioners"][0]["provisionerAddress"], 16)
    # updateConfig("unicastAddress", min(localUnicastAddr, uni) - 1)
    # 改成寫死 32767 = 7FFF,且不用-1 , 20211006改成不寫回測試看看, 20211026改成寫回測試看看
    updateConfig("unicastAddress", min(localUnicastAddr, 32767 ))

    deviceInfo = conf["deviceInfoData"]
    # sensorClientGroupAddress = None if "sensorClientGroupAddress" not in deviceInfo[0]["data"] else deviceInfo[0]["data"]["sensorClientGroupAddress"]
    groupInfoData = conf["groupInfoData"]
    groupChildNodeData = conf["groupChildNodeData"]
    sceneMainData = conf["sceneMainData"]
    sceneGroupDetailData = conf["sceneGroupDetailData"]
    sceneSingleDetailData = conf["sceneSingleDetailData"]
    sceneScheduleData = conf["sceneScheduleData"]
    sceneScheduleDetailData = conf["sceneScheduleDetailData"]
    provisionedData = conf["provisionedData"]
    meshName = provisionedData["meshName"]
    meshUUID = provisionedData["meshUUID"].replace('-', '')
    netKeys = provisionedData["netKeys"]
    if "nodes" in provisionedData:
        nodes = provisionedData["nodes"]
    else:
        nodes = []
    timestamp = int(provisionedData["timestamp"], 16)
    appKeys = provisionedData["appKeys"]
    provisioners = provisionedData["provisioners"]
    deviceUnicastAddress = int(provisioners[0]["provisionerAddress"], 16)
    dev.local_unicast_address_start = deviceUnicastAddress
    db.mesh_name = meshName
    db.mesh_UUID = mt._UUID(bytearray.fromhex(meshUUID))

    # 解析添加net keys
    net_keys = []
    for nk in netKeys:
        min_security = "low" if nk["minSecurity"] == 1 else "high"
        net_keys.append(mt.Netkey(nk["name"], nk["index"], nk["key"], min_security, nk["phase"]))
    db.net_keys = net_keys

    # 解析添加app keys
    app_keys = []
    for ak in appKeys:
        app_keys.append(mt.Appkey(ak["name"], ak["index"], ak["boundNetKey"], ak["key"]))
    db.app_keys = app_keys

    # 解析添加provisioners
    pros = []
    for pro in provisioners:
        unicastRanges = []
        for ur in pro["allocatedUnicastRange"]:
            lowAddr = max(provisionedData['nextUnicast'], ur["lowAddress"])
            unicastRanges.append(mt.UnicastRange(lowAddr, ur["highAddress"]))
        groupRanges = [mt.GroupRange(0xC000, 0xFEFF)]
        pros.append(mt.Provisioner(pro["provisionerName"], pro["UUID"].replace('-', ''), \
                                   groupRanges, unicastRanges))
    db.provisioners = pros

    myColorGroups = {}

    # 解析添加groups
    groups = []
    noneColorGroups = []
    last_group_id = 0

    sort_data = sorted(groupInfoData, key=lambda x: x["data"]["unicastAddress"])

    for g in sort_data:
        groups.append(mt.Group(g["data"]["name"], g["data"]["unicastAddress"], 0))
        if g["data"]["unicastAddress"] > last_group_id:
            last_group_id = g["data"]["unicastAddress"]
        ###noneColorGroups.append(mt.Group(g["data"]["name"] + "_0", g["data"]["unicastAddress"], 0))
        if "colorAddress" in g["data"]:
            ##groups.append(mt.Group(g["data"]["name"] + "_1", g["data"]["colorAddress"], 0))
            groups[len(groups) - 1].sub_group1 = g["data"]["colorAddress"]
            if g["data"]["unicastAddress"] > last_group_id:
                last_group_id = g["data"]["unicastAddress"]

    db.groups = groups
    myGroups = {}

    groupInfo = []
    for gid in groupInfoData:
        groupInfo.append(gid["data"])

    db.groupInfo = groupInfo

    # 群組明細資料
    groupDetail = []

    # 解析nodes subscribe groups
    nodesSubGroups = {}
    for gcn in groupChildNodeData:
        groupDetail.append(gcn["data"])
        nodeUnicastAddress = gcn["data"]["unicastAddress"]
        if str(nodeUnicastAddress) not in nodesSubGroups.keys():
            nodesSubGroups[str(nodeUnicastAddress)] = []
        for gi in groupInfoData:
            if gi['id'] == gcn['data']['groupID']:
                nodesSubGroups[str(nodeUnicastAddress)].append(gi['data']['unicastAddress'])
                break
    for gcn in groupChildNodeData:
        nodeUnicastAddress = gcn["data"]["unicastAddress"]
        for gi in groupInfoData:
            if gi['id'] == gcn['data']['groupID']:
                if gi['data']['unicastAddress'] not in myGroups.keys():
                    myGroups[gi['data']['unicastAddress']] = []
                myGroups[gi['data']['unicastAddress']].append(nodeUnicastAddress)

    for a_group in groups:
        if myGroups.get(a_group.address.real) != None:
            a_group.nodes_unicast_address = [x for x in myGroups[a_group.address.real]]

    # 群組明細資料 存到db
    db.groupDetail = groupDetail

    # 裝置資料
    deviceData = []
    for di in deviceInfo:
        deviceData.append(di["data"])
    db.deviceInfo = deviceData

    # 情境主檔資料
    sceneMain = []
    for smd in sceneMainData:
        sceneMain.append(smd["data"])
    db.sceneMain = sceneMain

    # 情境群組明細資料
    sceneGroupDetail = []
    for sgdd in sceneGroupDetailData:
        sceneGroupDetail.append(sgdd["data"])
    db.sceneGroupDetail = sceneGroupDetail

    # 情境單燈明細資料
    sceneSingleDetail = []
    for ssdd in sceneSingleDetailData:
        sceneSingleDetail.append(ssdd["data"])
    db.sceneSingleDetail = sceneSingleDetail

    # 情境定時主檔資料
    sceneSchedule = []
    for sshd in sceneScheduleData:
        sceneSchedule.append(sshd["data"])
    db.sceneSchedule = sceneSchedule

    # 情境定時明細資料
    sceneScheduleDetail = []
    for sshdd in sceneScheduleDetailData:
        sceneScheduleDetail.append(sshdd["data"])
    db.sceneScheduleDetail = sceneScheduleDetail

    nodesTmp = []
    for n in nodes:
        if n["UUID"] != "":
            UUIDNode = mt._UUID(bytearray.fromhex(n["UUID"].replace('-', '')))
        else:
            UUIDNode = mt._UUID(bytearray([0] * 16))
        deviceKeyNode = mt.Key(bytearray.fromhex(n["deviceKey"]))
        unicastAddressNode = mt.UnicastAddress(int(n["unicastAddress"], 16))
        cidNode = mt.Identifier(n["cid"])
        vidNode = mt.Identifier(n["vid"])
        pidNode = mt.Identifier(n["pid"])
        unicastAddressInt = int(n["unicastAddress"], 16)
        nodeName = n["name"]
        for di in deviceInfo:
            if di['data']['unicastAddress'] == unicastAddressInt:
                nodeName = di['data']['name']
                break
        netKeysNode = []
        for nk in n["netKeys"]:
            netKeysNode.append(mt.NetkeyState(nk["index"]))
        if "features" in n:
            featuresNode = mt.NodeFeatures(
                n["features"]["relay"],
                n["features"]["proxy"],
                n["features"]["friend"],
                n["features"]["lowPower"])
        else:
            featuresNode = None
        appKeysNode = n["appKeys"]
        appKeysNode = []
        for ak in n["appKeys"]:
            appKeysNode.append(mt.KeyIndex(int(ak["index"], 16)))
        elementsNode = []
        for e in n["elements"]:
            # index, location=0, models=[], unicast_address=None, name=""
            modelsNode = []
            for m in e["models"]:
                # model_id, subscribe=[], publish=None, bind=[], company_id=None
                modelIdM = int(m["modelId"], 16) & 0xffff
                nodeUnicastAddressStr = str(int(n["unicastAddress"], 16))
                # subscribeM = [] if "subscribe" not in m else m["subscribe"]
                subscribeM = []
                if e["index"] in [0, 1] and int(m["modelId"],
                                                16) >= 0x1000 and nodeUnicastAddressStr in nodesSubGroups.keys():
                    for msub in nodesSubGroups[nodeUnicastAddressStr]:
                        subscribeM.append(msub + int(e['index']))
                        # subscribeM.append('%04x' % (msub + int(e['index'])))
                publishM = None
                if "publish" in m:
                    publishAddress = m["publish"]["address"]
                    publishIndex = int(m["publish"]["index"], 16)
                    # ttl == 255 undefined
                    publishTTL = 1 if m["publish"]["ttl"] == 255 else m["publish"]["ttl"]
                    publishPeriod = m["publish"]["period"]
                    publishRetransmit = mt.unpack(mt.PublishRetransmit, \
                                                  (m["publish"]["retransmit"]["count"],
                                                   m["publish"]["retransmit"]["interval"]))
                    publishCredentials = m["publish"]["credentials"]
                    publishM = mt.Publish(publishAddress, publishIndex, publishTTL, \
                                          publishPeriod, publishRetransmit, publishCredentials)
                bindM = []
                # element0和element1中，modelId>=0x1000的model全部bind appkey0
                if e["index"] in [0, 1] and int(m["modelId"], 16) >= 0x1000:
                    bindM.append(mt.KeyIndex(0))
                # 搜寻所有elements，追加非0 appkeys
                if "bind" in m:
                    for ak in m["bind"]:
                        if ak != '0000':
                            bindM.append(mt.KeyIndex(int(ak, 16)))
                company_idM = None if len(m["modelId"]) <= 4 else int(m["modelId"][:4], 16)
                modelsNode.append(mt.Model(modelIdM, subscribeM, publishM, bindM, company_idM))
            elem = mt.Element(e["index"], e["location"], modelsNode)
            elementsNode.append(elem)
        crpl = None if ("crpl" not in n or n["crpl"] == "") else int(n["crpl"], 16)
        ttl = None if "ttl" not in n else n["ttl"]
        nodesTmp.append(mt.Node(UUIDNode, deviceKeyNode, unicastAddressNode, \
                                netKeysNode, n["configComplete"], n["security"], \
                                # netKeysNode, n["configComplete"], mt.SecurityLevel(n["security"]), \
                                nodeName, cidNode, vidNode, pidNode, crpl, \
                                None, None, featuresNode, elementsNode, appKeysNode, None, ttl))
    db.nodes = nodesTmp
    db.store()

    # 设置subnetkey和appkey
    dev.send(cmd.StateClear())
    time.sleep(3)
    dev.send(cmd.RadioReset())
    time.sleep(3)
    print("Import Config Complete! Please ReStart Your Machine!")

    if removeFile:
        os.remove(configFile)