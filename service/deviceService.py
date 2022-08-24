import sys
import os
import time
import traceback
from datetime import datetime
from threading import Timer
import json
import base64
import uuid as uuid_tool
from threading import Lock

from pyaci.interactive import Interactive
from .properties import Proerties
from .dataDao import DataDao
import shutil

from pyaci.aci.aci_uart import Uart
from pyaci.mesh.provisioning import Provisioner, Provisionee
from pyaci.mesh import types as mt
from pyaci.mesh.database import MeshDB
from pyaci.models.config import ConfigurationClient
from pyaci.models.generic_on_off import GenericOnOffClient
from pyaci.models.generic_on_off_flash import GenericOnOffFlashClient
from pyaci.models.vendor_model_message import VendorModelMessageClient
from pyaci.models.lsbu import LsbuClient
from pyaci.models.generic_level import GenericLevelClient

from pyaci.aci import aci_cmd as cmd
from pyaci.mesh.access import AccessStatus
from pyaci.models.sensor import SensorClient
from pyaci.aci.aci_evt import Event

from pyaci.models.time import TimeClient
from pyaci.models.scene import SceneClient
from pyaci.models.scheduler import SchedulerClient
import pyaci.aci.aci_evt as evt

this_file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,this_file_dir+'/..')
import globalvar as gl

import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter

#控燈後是否會寫回狀態(True:會寫入DB,False:不會寫入DB)
testSaveDb = gl.get_value('testSaveDb')

#是否會訂閱Group(True:會Subscription ,False:不會Subscription)
SUB_STATUS = gl.get_value('SUB_STATUS')

class DeviceService():
    _instance = None

    ALL_GROUP_ID = 0xc000
    DEFULT_GROUP_ID = 0xc010
    DEFULT_SENSOR_GROUP_ID = 0xd010

    TYPE_SINGLE_LIGHT = 1
    TYPE_GROUP = 3
    TYPE_SENSOR_GROUP = 4
    TYPE_SCENE = 5

    MIN_DEVKEY_HANDLE_ID = 8
    MAX_DEVKEY_HANDLE_ID = 17

    os_path = os.path.split(os.path.realpath(__file__))[0]
    database_path = os_path + '/../pyaci/database/example_database.json'

    import_json = os_path + "/../pyaci/data/LTDMS.json"

    IMG_PATH = os_path + '/../static/images/avatar/'

    SCEHDULE_LIGHT_ACTION = {"off": 0, "on": 1, "none": 15,
                             0: "off", 1: "on", 15: "none"}

    WEEK_MAP = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1, 7: 0}

    # DEV_DEFAULT_NAME = "DT6"

    FREEZE_SCENE_ID = 65535

    # key : pid_vid
    product_maps = {
        "0001_0001": "DT6",
        "0001_0002": "DT8",
        "0001_0003": "REPEATER",
        "0003_0001": "DT6",
        "0003_0002": "DT8",
        "0003_0003": "DUC",
        "0004_0001": "DT6",
        "0004_0002": "DT8",
        "0004_0003": "DUC",
        "0005_0001": "SW1/SW3/SW6",
        "0005_0002": "SW4",
        "0005_0003": "SW15",
        "0005_0004": "SW1",
        "0005_0005": "SW6",
        "0006_0001": "DT6",
        "0006_0002": "DT8",
        "0006_0003": "DUC",
        "0007_0001": "DT6",
        "0007_0002": "DT8",
        "0007_0003": "DUC",
        "0008_0001": "OPLUG",
        "00D3_0C1F": "MC_WONG_UART",
        "00D3_123F": "TruBluSensorSwitch",
        "00E1_0001": "ALS"
    }

    @staticmethod
    def get_instance():
        if DeviceService._instance is None:
            DeviceService()
        return DeviceService._instance

    @staticmethod
    def get_instance2(myDEFAULT_LOCAL_UNICAST_ADDRESS_START):
        if DeviceService._instance is None:
            DeviceService(myDEFAULT_LOCAL_UNICAST_ADDRESS_START=myDEFAULT_LOCAL_UNICAST_ADDRESS_START)
        return DeviceService._instance

    @staticmethod
    def clear():
        if DeviceService._instance is not None:
            DeviceService._instance.doClose()
            DeviceService._instance = None




    def __init__(self,myDEFAULT_LOCAL_UNICAST_ADDRESS_START=0):

        self.device = None

        self.db = None
        self.dataDao = DataDao.get_instance()       #建立light資料庫存config裡面的資料（不是config.ini）
        self.gc = None
        self.gcf = None
        self.vmm = None
        self.cc = None
        self.provisioning = None
        self.glc = None
        self.ssc = None
        self.sc = None
        self.srsc = None
        self.src = None
        self.sdc = None
        self.sdsc = None
        self.tsc = None
        self.tc = None
        self.is_busy = False
        self.lc = None

        self.last_address_handle = None
        self.last_address_handle_id = None
        self.last_devkey_handle = None
        self.last_devkey_handle_id = None

        self.sensor_group_ary = None
        print("DeviceService._instance")
        if DeviceService._instance is not None:
            raise Exception('only one instance can exist')
        else:
            DeviceService._instance = self

        self.lock = Lock()

        self.doInitDivice(myDEFAULT_LOCAL_UNICAST_ADDRESS_START)
        self.run_sensor = -1
        self.run_monitor = -1
        self.dataDao.clearAll()
        self.syncJsonToDB()

        self.server_need_login = True
        self.server_password_base64 = ""

        self.response = None
        self.resp_login = requests.Session()
        self.resp_login.mount('http://', HTTPAdapter(max_retries=3))
        self.resp_get = requests.Session()
        self.resp_get.mount('http://', HTTPAdapter(max_retries=3))
        self.resp_put = requests.Session()
        self.resp_put.mount('http://', HTTPAdapter(max_retries=3))

    def clear_dataDao(self):
        if self.dataDao is not None:
            self.dataDao.clear()
            self.dataDao = None

    def setTTL(self,newTTL):
        AccessStatus.setTTL(newTTL)

    def syncJsonToDB(self):
        alist = self.dataDao.queryLights(DeviceService.TYPE_SINGLE_LIGHT)
        if len(self.db.nodes) > 0:
            # single light
            for a_node in self.db.nodes:
                is_temperature = 0
                if len(a_node.elements) > 1 and a_node.elements[1].models is not None:
                    model_1002_ary = [x for x in a_node.elements[1].models if x.model_id.model_id == int("1002", 16)]
                    if len(model_1002_ary) > 0:
                        is_temperature = 1
                print("a_node.unicast_address:"+str(a_node.unicast_address))
                self.dataDao.saveLight(a_node.unicast_address, DeviceService.TYPE_SINGLE_LIGHT, is_temperature)

            # group
            for a_group in self.db.groups:
                self.dataDao.saveLight(a_group.address, DeviceService.TYPE_GROUP, 1)

            # B: scene,schedule,
            self.loadSceneScheduleFromLTDMS()

    def loadSceneScheduleFromLTDMS(self):
        scene_data = {}
        sceneGroupDetailData = self.db.sceneGroupDetail

        if sceneGroupDetailData is not None:
            # print("sceneGroupDetailData:"+str(sceneGroupDetailData))
            for a_group in sceneGroupDetailData:
                scene_id = a_group.scene_num

                if scene_data.get(scene_id) == None:
                    scene_data[scene_id] = {
                        "a_time": a_group.dimming_trans_steps * a_group.dimming_trans_time,
                        "a_level": 0,
                    }
                else:
                    scene_data[scene_id]["a_time"] = a_group.dimming_trans_steps * a_group.dimming_trans_time

                self.dataDao.saveSceneLightStatus(scene_id, a_group.group_address, DeviceService.TYPE_GROUP,
                                                  1 if a_group.switch_state else 0,
                                                  a_group.dimming_value, a_group.color_value)

                group_obj = self.getGroupByAddress(a_group.group_address)

                if group_obj is not None:
                    for light_id in group_obj.nodes_unicast_address:
                        self.dataDao.saveLightSceneRelation(light_id, a_group.group_address, scene_id)

        sceneMainData = self.db.sceneMain

        if sceneMainData is not None:
            for a_main_scene in sceneMainData:
                scene_id = a_main_scene.scene_num
                scene_name = a_main_scene.scene_name
                a_time = 0
                a_level = 0
                if scene_data.get(scene_id) != None:
                    a_time = scene_data[scene_id]["a_time"]
                    a_level = scene_data[scene_id]["a_level"]

                self.dataDao.saveScene(scene_id, scene_name, a_time, a_level, None)

        sceneSingleDetailData = self.db.sceneSingleDetail

        if sceneSingleDetailData is not None:
            # print("sceneSingleDetailData:"+str(sceneSingleDetailData))
            for a_single_scene in sceneSingleDetailData:
                # print("a_single_scene:" + str(a_single_scene))
                scene_id = a_single_scene.scene_num
                light_id = a_single_scene.single_address
                state = 1 if a_single_scene.switch_state else 0
                lightness_per = a_single_scene.dimming_value
                temperature_per = a_single_scene.color_value
                if a_single_scene.group_address == 0:
                    self.dataDao.saveSceneLightStatus(scene_id, light_id, DeviceService.TYPE_SINGLE_LIGHT,state, lightness_per, temperature_per)

        main_data_map = {}

        sceneScheduleDetailData = self.db.sceneScheduleDetail
        # print("sceneScheduleDetailData:"+str(sceneScheduleDetailData))
        if sceneScheduleDetailData is not None:
            for a_detail_schedule in sceneScheduleDetailData:
                light_id = a_detail_schedule.single_address
                group_id = -1
                schedule_id = a_detail_schedule.schedule_num
                data_id = a_detail_schedule.schedule_id
                main_data_map[data_id] = schedule_id
                scene_id = a_detail_schedule.scene_num
                # if scene_id == 0:
                #     self.dataDao.saveLightScheduleRelation(light_id, group_id, -1, schedule_id)
                # else:
                #     scene_light_status_list = self.dataDao.querySceneLightStatusList(scene_id)
                #
                #     group_id_ary = [x.address for x in self.db.groups if light_id in x.nodes_unicast_address]
                #     for a_data in scene_light_status_list:
                #         if a_data["light_id"] in group_id_ary:
                #             self.dataDao.saveLightScheduleRelation(light_id, a_data["light_id"], scene_id, schedule_id)

            # schedule_relation_list = self.dataDao.queryAllScheduleRelationList()
            # # print("schedule_relation_list:"+str(schedule_relation_list))
            # for a_detail_schedule in sceneScheduleDetailData:
            #     light_id = a_detail_schedule.single_address
            #     schedule_id = a_detail_schedule.schedule_num
            #     data_id = a_detail_schedule.schedule_id
            #     main_data_map[data_id] = schedule_id
            #     scene_id = a_detail_schedule.scene_num
            #     has_it = 0
            #     for a_schedule_relation in schedule_relation_list:
            #         old_light_id = a_schedule_relation["light_id"]
            #         old_scene_id = a_schedule_relation["scene_id"]
            #         if old_light_id == light_id and old_scene_id == scene_id:
            #             has_it = 1
            #     if has_it == 0:
            #         ##把單燈也加入 ScheduleRelation
            #         self.dataDao.saveLightScheduleRelation(light_id, 0, scene_id, schedule_id)

        sceneScheduleData = self.db.sceneSchedule

        if sceneScheduleData is not None:
            for a_main_schedule in sceneScheduleData:

                data_id = a_main_schedule.id
                a_week = a_main_schedule.repeat_weekly
                a_time = a_main_schedule.start_time.split(":")

                if a_week == "":
                    continue

                else:
                    # print("a_week:" + str(a_week) )
                    weeks  = "1" if len(a_week) >= 7 and int(a_week[6:7]) == 1 else ""
                    weeks += "2" if len(a_week) >= 6 and int(a_week[5:6]) == 1 else ""
                    weeks += "3" if len(a_week) >= 5 and int(a_week[4:5]) == 1 else ""
                    weeks += "4" if len(a_week) >= 4 and int(a_week[3:4]) == 1 else ""
                    weeks += "5" if len(a_week) >= 3 and int(a_week[2:3]) == 1 else ""
                    weeks += "6" if len(a_week) >= 2 and int(a_week[1:2]) == 1 else ""
                    weeks += "7" if len(a_week) >= 1 and int(a_week[0:1]) == 1 else ""

                    week_str = ",".join([x for x in weeks])

                    hours = int(a_time[0])
                    mins = int(a_time[1])
                    scene_id = a_main_schedule.scene_num
                    if main_data_map.get(data_id) == None:
                        continue

                    if scene_id == 0:
                        action = 0
                        schedule_name = "schedule_" + str(data_id)
                        self.dataDao.saveSchedule(data_id, main_data_map[data_id], DeviceService.TYPE_SINGLE_LIGHT,
                                                  light_id, -1, schedule_name, action, week_str, hours, mins)
                    else:
                        schedule_name = a_main_schedule.schedule_name
                        self.dataDao.saveSchedule(data_id, main_data_map[data_id], DeviceService.TYPE_SCENE, -1, scene_id,
                                                  schedule_name, 2, week_str, hours, mins)

    # 安房
    def call_house_API(self, object_reference, api_value):
        fake_json = False
        '''
        # Log in only need once, and it has been connected to the server, so when send command
        # like request.Get, Put... will not cause log out otherwise will occur log out everytime. '''
        if self.server_need_login:
            self.response = None
            try:
                server_password = gl.get_value("server_username")+":"+gl.get_value("server_password")
                self.server_password_base64 = (base64.b64encode(server_password.encode("UTF-8"))).decode("UTF-8")
                if gl.get_value('MORE_LOG'):
                    print("server_password_base64", self.server_password_base64)
                # resp = requests.get("http://" + gl.get_value("server_ip") + "/enteliweb/api/auth/basiclogin?alt=json",
                #     auth=HTTPBasicAuth("Basic", self.server_password_base64))
                self.response = self.resp_login.get("http://" + gl.get_value("server_ip") + "/enteliweb/api/auth/basiclogin?alt=json",
                    auth=HTTPBasicAuth(gl.get_value("server_username"), gl.get_value("server_password")))
                if gl.get_value('MORE_LOG'):
                    print("get basiclogin:", self.response.status_code, self.response.text)
                resp_text = self.response.text
                if fake_json:
                    resp_text = '{"$base":"String","value":"OK","_csrfToken":"ZBKkZQFfGoawDn42Jg0OmxV4OQ4nFxH6UEMNnW3E"}'
                resp_json = json.loads(resp_text)
                if gl.get_value('MORE_LOG'):
                    print("resp_json value:", resp_json["value"])
                if resp_json["value"] == "OK":
                    self.server_need_login = False
            except requests.exceptions.RequestException as e:
                print("[call_house_API] login exception: ", e)

        if self.server_need_login:
            if gl.get_value('MORE_LOG'):
                print("server_need_login")
        else:
            # resp = requests.get("http://" + gl.get_value("server_ip") + "/enteliweb/api/.bacnet/"+gl.get_value("server_sitename")+"/"+gl.get_value("server_device_number")+"/binary-value,"+object_reference+"/present-value?alt=json",
            #                     auth=HTTPBasicAuth("Basic", self.server_password_base64))
            '''
            # This is to get object_reference's base. '''
            try:
                resp1 = self.resp_get.get("http://" + gl.get_value("server_ip") + "/enteliweb/api/.bacnet/"+gl.get_value("server_sitename")+"/"+gl.get_value("server_device_number")+"/binary-value,"+ object_reference +"/present-value?alt=json",
                                    auth=HTTPBasicAuth(gl.get_value("server_username"), gl.get_value("server_password")),
                                    cookies=self.response.cookies)
                if gl.get_value('MORE_LOG'):
                    print("get bacnet:", resp1.status_code, resp1.text)
                resp_text = resp1.text
                if fake_json:
                    resp_text = '{"$base":"Enumerated","value":"Active"}'
                resp_json = json.loads(resp_text)
                if gl.get_value('MORE_LOG'):
                    print("resp_json $base:", resp_json["$base"])
            except requests.exceptions.RequestException as e:
                self.server_need_login = True
                print("[call_house_API] request Get exception: ", e)
            # resp2 = requests.put("http://" + gl.get_value("server_ip") + "/enteliweb/api/.bacnet/"+gl.get_value("server_sitename")+"/"+gl.get_value("server_device_number")+"/binary-value,"+object_reference+"/present-value?alt=json",
            #     json={
            #         "$base": resp_json["$base"],
            #         "value": api_value
            #     },
            #     auth=HTTPBasicAuth("Basic", self.server_password_base64))
            '''
            # Send the data to the web base on the info from previous "base". '''
            try:
                resp2 = self.resp_put.put("http://" + gl.get_value("server_ip") + "/enteliweb/api/.bacnet/"+gl.get_value("server_sitename")+"/"+gl.get_value("server_device_number")+"/binary-value,"+ object_reference +"/present-value?alt=json",
                    json={
                        "$base": resp_json["$base"],
                        "value": api_value
                    },
                    auth=HTTPBasicAuth(gl.get_value("server_username"), gl.get_value("server_password")),
                    cookies=self.response.cookies)
                if gl.get_value('MORE_LOG'):
                    print("put bacnet:", resp2.status_code, resp2.text)
            except requests.exceptions.RequestException as e:
                self.server_need_login = True
                print("[call_house_API] request put exception: ", e)


    def call_iBeacon_sensor_info_API(self, sensorMap):
        rssi = sensorMap["data_rssi"]
        if gl.get_value('MORE_LOG') and False:
            print('call_iBeacon_sensor_API rssi value: ', rssi, ' time: ', str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        #todo..

    def call_Energy_log_API(self, uniAddr, dic_hour_value):
        '''
        # dic_hour_value[0]: is the closest log from now
        # EX: (if got 2 hours info from fw)
          now is 16:30
          dic_hour_value[0] = 16:00 ~ 16:30's log <--- right now
          dic_hour_value[1] = 15:00 ~ 16:00's log <--- not changed
        '''
        if gl.get_value('MORE_LOG'):
            print("call_Energy_log_API hour value: ", dic_hour_value[0])
            print("call_Energy_log_API hour value: ", dic_hour_value[1])

        #todo


    def callback_house_open_door(self,value,unicast_address):
        if gl.get_value('MORE_LOG'):
            print('callback_house_open_door value: ', str(value) )
            print('callback_house_open_door unicast_address: ', str(unicast_address) )
        device = self.getDeviceInfoData(unicast_address)
        if device is not None:
            if gl.get_value('MORE_LOG'):
                print('callback_house_open_door device.name: '+device.name )
                server_ip = gl.get_value("server_ip")
                server_username = gl.get_value("server_username")
                server_password = gl.get_value("server_password")
                print('callback_house_open_door server_ip: '+server_ip )
                print('callback_house_open_door server_username: '+server_username )
                print('callback_house_open_door server_password: '+server_password )

            object_reference = gl.get_object_reference( str(device.name).lower() )
            if object_reference is not None:
                if gl.get_value('MORE_LOG'):
                    print('callback_house_open_door object_reference: ' + object_reference)
                if object_reference is not None:
                    api_value = "inactive"
                    if str(value) == "1":
                        api_value = "active"
                    self.call_house_API(object_reference, api_value)



    def callback_iBeacon_sensor_info(self, sensorMap):
        if gl.get_value('MORE_LOG'):
            print('callback_iBeacon_sensor_info' + 'major ID: ', str(sensorMap["data_majorID"]) + ' ,minor ID:', str(sensorMap["data_minorID"]))
            print('callback_iBeacon_sensor_info unicast_address: ', str(sensorMap["src"]))
            print('callback_iBeacon_sensor_info dist: ', str(sensorMap["data_ImprovedDistance"]))
            print('callback_iBeacon_sensor_info RSSI: ', str(sensorMap["data_rssi"]))
        device = self.getDeviceInfoData(sensorMap["src"])
        if device is not None:
            if gl.get_value('MORE_LOG'):
                print('callback_iBeacon_sensor_info device.name: ' + device.name)

        self.call_iBeacon_sensor_info_API(sensorMap)


    def callbackC000(self,on_off,unicast_address):
        if gl.get_value('MORE_LOG'):
            print('callbackC000 on_off: ', on_off )
            print('callbackC000 unicast_address: ', str(unicast_address) )
        device = self.getDeviceInfoData(unicast_address)
        if device is not None:
            if on_off:
                device.switch_state = 1
            else:
                device.switch_state = 0
            self.updateDeviceInfo(device)
            if gl.get_value('MORE_LOG'):
                print("updateDeviceInfo switch_state ok")

    def callbackC001(self,lightness,unicast_address):
        if gl.get_value('MORE_LOG'):
            print('callbackC000 lightness: ', lightness )
            print('callbackC000 unicast_address: ', str(unicast_address) )

        temperature_per = int(255*(lightness + 32768)/65535)
        if gl.get_value('MORE_LOG'):
            print("temperature_per:"+str(temperature_per))
        device = self.getDeviceInfoData(unicast_address)
        if device is not None:
            device.dimming_value = temperature_per
            self.updateDeviceInfo(device)
            if gl.get_value('MORE_LOG'):
                print("updateDeviceInfo dimming_value ok")
        else:
            device = self.getDeviceInfoData(int(unicast_address-1))
            if device is not None:
                device.color_value = temperature_per
                self.updateDeviceInfo(device)
                if gl.get_value('MORE_LOG'):
                    print("updateDeviceInfo color_value ok")

    def callback_group_onoff(self,on_off, address_id):
        if gl.get_value('MORE_LOG'):
            print('callback_group_onoff on_off: ', on_off)
            print('callback_group_onoff address_id: ', str(address_id))
        group = self.getGroupInfoData(address_id)
        if on_off == 1:
            group.switch_state = True
        else:
            group.switch_state = False
        self.updateGroupInfo(group)
        if gl.get_value('MORE_LOG'):
            print("updateGroupInfo on_off ok")

        group2 = self.getGroup(address_id)
        devices = [device for device in group2['device']
                   if device['inUse'] == True]
        for device in devices:
            if gl.get_value('MORE_LOG'):
                print("device.id:" + str(device["id"]))
            device2 = self.getDeviceInfoData(device["id"])
            if device2 is not None:
                if on_off == 1:
                    device2.switch_state = 1
                else:
                    device2.switch_state = 0
                self.updateDeviceInfo(device2)
                if gl.get_value('MORE_LOG'):
                    print("updateDeviceInfo on_off ok")


    def callback_group_lightness(self,lightness,address_id):
        if gl.get_value('MORE_LOG'):
            print('callback_group_lightness lightness: ', lightness )
            print('callback_group_lightness address_id: ', str(address_id) )
        lightness_per = int(255*(lightness + 32768)/65535)
        if gl.get_value('MORE_LOG'):
            print("lightness_per:"+str(lightness_per))
        group = self.getGroupInfoData(address_id)
        group.dimming_value = lightness_per
        self.updateGroupInfo(group)
        if gl.get_value('MORE_LOG'):
            print("updateGroupInfo lightness ok")

        group2 = self.getGroup(  address_id )
        devices = [device for device in group2['device']
                   if device['inUse'] == True]
        for device in devices:
            if gl.get_value('MORE_LOG'):
                print( "device.id:"+ str(device["id"]) )
            device2 = self.getDeviceInfoData(device["id"])
            if device2 is not None:
                device2.dimming_value = lightness_per
                self.updateDeviceInfo(device2)
                if gl.get_value('MORE_LOG'):
                    print("updateDeviceInfo lightness ok")


    def callback_group_temperature(self,temperature,address_id):
        if gl.get_value('MORE_LOG'):
            print('callback_group_temperature temperature: ', temperature )
            print('callback_group_temperature address_id: ', str(address_id) )
        temperature_per = int(255*(temperature + 32768)/65535)
        if gl.get_value('MORE_LOG'):
            print("temperature_per:"+str(temperature_per))
        group_obj = self.getGroupByAddress(address_id)
        if group_obj.sub_group1 == None:
            return
        group = self.getGroupInfoData(address_id)
        group.color_value = temperature_per
        self.updateGroupInfo(group)
        if gl.get_value('MORE_LOG'):
            print("updateGroupInfo temperature ok")

        group2 = self.getGroup(  address_id )
        devices = [device for device in group2['device']
                   if device['inUse'] == True]
        for device in devices:
            if gl.get_value('MORE_LOG'):
                print( "device.id:"+ str(device["id"]) )
            device2 = self.getDeviceInfoData(device["id"])
            if device2 is not None:
                device2.color_value = temperature_per
                self.updateDeviceInfo(device2)
                if gl.get_value('MORE_LOG'):
                    print("updateDeviceInfo temperature ok")

    def callback_switch_onoff(self, on_off, data, src_unicast_addr, dst_address_id):
        transition_time_value = int(data[4], 16)
        repeat_value = 5
        ack = 0

        device = self.getDeviceInfoData(src_unicast_addr)
        if gl.get_value('MORE_LOG'):
            print('callback_switch_onoff device_name: ', device.name)
            print('callback_switch_onoff on_off: ', on_off )
            print('callback_switch_onoff src_unicast_addr: ', str(src_unicast_addr))
            print('callback_switch_onoff dst_address_id: ', str(dst_address_id))

        time.sleep(1)


        #temporary marked for debug
        group_info_data = self.setGroupOnOff(int(dst_address_id), on_off, transition_time_value, repeat_value, ack)
        if group_info_data.switch_state:
            print('set group onoff on is ok')
        else:
            print('set group onoff off is ok')


        ''' Update the lastest state to database. '''
        group = self.getGroupInfoData(dst_address_id)
        if on_off == 1:
            group.switch_state = True
        else:
            group.switch_state = False
        self.updateGroupInfo(group)
        if gl.get_value('MORE_LOG'):
            print("updateGroupInfo on_off ok")

        group2 = self.getGroup(dst_address_id)
        devices = [device for device in group2['device']
                   if device['inUse'] == True]
        for device in devices:
            if gl.get_value('MORE_LOG'):
                print("device.id:" + str(device["id"]) )
            device2 = self.getDeviceInfoData(device["id"])
            if device2 is not None:
                if on_off == 1:
                    device2.switch_state = 1
                else:
                    device2.switch_state = 0
                self.updateDeviceInfo(device2)
                if gl.get_value('MORE_LOG'):
                    print("updateDeviceInfo on_off ok")


    def callback_switch_lightness(self,lightness,address_id):
        if gl.get_value('MORE_LOG'):
            print('callback_switch_lightness lightness: ', lightness )
            print('callback_switch_lightness address_id: ', str(address_id) )
        lightness_per = int(255*(lightness + 32768)/65535)
        if gl.get_value('MORE_LOG'):
            print("lightness_per:"+str(lightness_per))
        group = self.getGroupInfoData(address_id)
        group.dimming_value = lightness_per
        self.updateGroupInfo(group)
        if gl.get_value('MORE_LOG'):
            print("updateGroupInfo lightness ok")

        group2 = self.getGroup(  address_id )
        devices = [device for device in group2['device']
                   if device['inUse'] == True]
        for device in devices:
            if gl.get_value('MORE_LOG'):
                print( "device.id:"+ str(device["id"]) )
            device2 = self.getDeviceInfoData(device["id"])
            if device2 is not None:
                device2.dimming_value = lightness_per
                self.updateDeviceInfo(device2)
                if gl.get_value('MORE_LOG'):
                    print("updateDeviceInfo lightness ok")


    def callback_switch_temperature(self,temperature,address_id):
        if gl.get_value('MORE_LOG'):
            print('callback_switch_temperature temperature: ', temperature )
            print('callback_switch_temperature address_id: ', str(address_id) )
        temperature_per = int(255*(temperature + 32768)/65535)
        if gl.get_value('MORE_LOG'):
            print("temperature_per:"+str(temperature_per))
        group_obj = self.getGroupByAddress(address_id)
        if group_obj.sub_group1 == None:
            return
        group = self.getGroupInfoData(address_id)
        group.color_value = temperature_per
        self.updateGroupInfo(group)
        if gl.get_value('MORE_LOG'):
            print("updateGroupInfo temperature ok")

        group2 = self.getGroup(  address_id )
        devices = [device for device in group2['device']
                   if device['inUse'] == True]
        for device in devices:
            if gl.get_value('MORE_LOG'):
                print( "device.id:"+ str(device["id"]) )
            device2 = self.getDeviceInfoData(device["id"])
            if device2 is not None:
                device2.color_value = temperature_per
                self.updateDeviceInfo(device2)
                if gl.get_value('MORE_LOG'):
                    print("updateDeviceInfo temperature ok")


    def callback_energy_log(self, src_address, hours, bData, compositionData, powerRatio):
        if gl.get_value('MORE_LOG'):
            print("callback_energy_log unicast address is: ", src_address)
            print("callback_energy_log composition PID is: ", compositionData[str(src_address)]['productId'])
            print("callback_energy_log powerRatio is: ", powerRatio[str(src_address)])

        # power walt correspond to PID
        # 15W , 35W , default = 40W
        if compositionData[str(src_address)]['productId'] == 3:
            maxPower = 15
        elif compositionData[str(src_address)]['productId'] == 4:
            maxPower = 35
        else:
            maxPower = 40

        # Power depend on ratio if is qualified.
        if powerRatio[str(src_address)] > 0 and powerRatio[str(src_address)] <= 100 and powerRatio != {}:
            maxPower = maxPower * powerRatio[str(src_address)]/100

        for i in range(hours):
            bData[str(src_address)]['hours']['value'][i] = round(bData[str(src_address)]['hours']['value'][i] * maxPower * 1000 / (100*60*60), 2)

        self.call_Energy_log_API(src_address, bData[str(src_address)]['hours']['value'])



    # def doGetDivice(self):
    #     if self.device == None:
    #         self.device = Interactive(Uart(port=Proerties.dev_com,
    #                                        baudrate=Proerties.dev_baudrate,
    #                                        device_name=Proerties.dev_com.split("/")[-1]))
    #         # send = self.device.acidev.write_aci_cmd  # NOQA: Ignore unused variable
    #
    #         self.db = MeshDB(DeviceService.database_path)
    #         print("db:" + str(self.db))
    #         print("self.db.provisioners:" + str(self.db.provisioners))
    #
    #         self.provisioning = Provisioner(self.device, self.db)
    #
    #     return self.device

    def doInitDivice(self,myDEFAULT_LOCAL_UNICAST_ADDRESS_START=0):

        if self.device == None:
            if myDEFAULT_LOCAL_UNICAST_ADDRESS_START > 0:
                self.device = Interactive(Uart(port=Proerties.dev_com,
                                               baudrate=Proerties.dev_baudrate,
                                               device_name=Proerties.dev_com.split("/")[-1]),myDEFAULT_LOCAL_UNICAST_ADDRESS_START=myDEFAULT_LOCAL_UNICAST_ADDRESS_START)
            else:
                self.device = Interactive(Uart(port=Proerties.dev_com,
                                               baudrate=Proerties.dev_baudrate,
                                               device_name=Proerties.dev_com.split("/")[-1]))
            # send = self.device.acidev.write_aci_cmd  # NOQA: Ignore unused variable

            #從example_jsonxxx.db檔案中載入mesh network database
            self.db = MeshDB(DeviceService.database_path)
            print("db:" + str(self.db))
            print("self.db.provisioners:" + str(self.db.provisioners))

            #將mesh database的資料送給local address
            self.provisioning = Provisioner(self.device, self.db)


        self.removeAddressHandle()
        self.removeDevkeyHandle()

        cmd.init_my_sub_group_list()

        if gl.get_value("SUB_STATUS"):
            self.doChangeSubStatus(gl.get_value("SUB_STATUS"))

        '''
        1. 建立一個configuration client model的類別
        2. 將此類別加入到裝置中
        '''
        if self.cc == None:
            self.cc = ConfigurationClient(self.db)
            self.device.model_add(self.cc)

        now_dongle_address = self.device.DEFAULT_LOCAL_UNICAST_ADDRESS_START
        print("now_dongle_address:" + str(now_dongle_address) )

        self.device.setC0000(self.callbackC000)
        self.device.setC0001(self.callbackC001)

        self.device.set_my_sub_group_list(cmd.get_my_sub_group_list())
        self.device.set_my_sub_group_address_handle_list(cmd.get_my_sub_group_address_handle_list())

        self.device.set_callback_group_onoff(self.callback_group_onoff)
        self.device.set_callback_group_lightness(self.callback_group_lightness)
        self.device.set_callback_group_temperature(self.callback_group_temperature)
        # switch control server.
        self.device.set_callback_switch_onoff(self.callback_switch_onoff)
        self.device.set_callback_switch_lightness(self.callback_switch_lightness)
        self.device.set_callback_switch_temperature(self.callback_switch_temperature)

        self.device.set_callback_house_open_door(self.callback_house_open_door)
        self.device.set_callback_iBeacon_sensor_info(self.callback_iBeacon_sensor_info)


        # print("doInitDivice: end" )

    def doChangeSubStatus(self,newSUB_STATUS):
        if gl.get_value("MORE_LOG"):
            print("doChangeSubStatus:"+str(newSUB_STATUS))

        if newSUB_STATUS:
            cmd.init_my_sub_group_list()
            self.device.send(cmd.AddrSubscriptionAdd(0xc000))
            time.sleep(2)
            self.device.send(cmd.AddrSubscriptionAdd(0xc001))
            time.sleep(2)
            self.device.send(cmd.AddrSubscriptionAdd(0xc002))
            time.sleep(2)
            self.device.send(cmd.AddrSubscriptionAdd(0xcfff))
            time.sleep(2)

            # print("=================================AddrLocalUnicastGet start")
            # self.device.send(cmd.AddrLocalUnicastGet())
            # print("=================================AddrLocalUnicastGet end")

            # print("=================================heartbeat test start")
            if self.cc == None:
                self.cc = ConfigurationClient(self.db)
                self.device.model_add(self.cc)

            # print("=================================heartbeat test end 1")
            now_dongle_address = self.device.DEFAULT_LOCAL_UNICAST_ADDRESS_START
            print("now_dongle_address:" + str(now_dongle_address))
            # result_devices = self.getDeviceInfoList()
            # for tmpdevice in result_devices:
            #     uniAddress = tmpdevice["uniAddress"]
            #     self.device.send(cmd.AddrPublicationAdd(uniAddress))
            #     time.sleep(2)
            #
            #     address_handle = self.getAddressHandle(uniAddress)
            #     devkey_handle = self.getDevkeyHandle(uniAddress)
            #     print("getConfigurationClient_heartbeat_publication_set uniAddress:"+str(uniAddress))
            #     print("getConfigurationClient_heartbeat_publication_set address_handle:"+str(address_handle))
            #     print("getConfigurationClient_heartbeat_publication_set devkey_handle:"+str(devkey_handle))
            #     self.cc.publish_set(devkey_handle, address_handle)
            #     print("=================================heartbeat publication start")
            #     self.cc.heartbeat_publication_set2( 0xC000 , 16)
            #     time.sleep(0.5)
            #     print("=================================heartbeat subscription start")
            #     self.cc.heartbeat_subscription_set( now_dongle_address , 0xC000, 16)
            #     time.sleep(0.5)
            #     print("=================================heartbeat subscription end")

            # print("=================================heartbeat test end 2")

            # self.cc.publish_set(8, 0)
            # self.cc.heartbeat_subscription_set(32618, 49152, 64)
            # time.sleep(1)
            # print("=================================heartbeat test end 3")

            #
            # time.sleep(2)
            # self.device.send(cmd.AddrSubscriptionRemove(0))
            # time.sleep(2)
            # self.device.send(cmd.AddrSubscriptionRemove(1))
            # time.sleep(2)
            # self.device.send(cmd.AddrSubscriptionRemove(2))
            #
            #
            result_groups = self.getGroupList()
            for group in result_groups:
                # print("group:" + str(group))
                group_address = group['id']
                time.sleep(1)
                # print("AddrSubscriptionAdd start")
                # print("AddrSubscriptionAdd0:" + str(group_address))
                self.device.send(cmd.AddrSubscriptionAdd(group_address))
                self.device.set_my_sub_group_list_type(group_address, "base0")
                time.sleep(1)
                # print("AddrSubscriptionAdd1:" + str(group_address+1))
                self.device.send(cmd.AddrSubscriptionAdd(group_address + 1))
                self.device.set_my_sub_group_list_type(group_address + 1, "base1")
                time.sleep(1)
                # print("AddrSubscriptionAdd2:" + str(group_address+2))
                self.device.send(cmd.AddrSubscriptionAdd(group_address + 2))
                self.device.set_my_sub_group_list_type(group_address + 2, "base2")

            # 要等時間,怕太快會還沒拿到address_handle的數值
            time.sleep(1)
            print(cmd.get_my_sub_group_list())
            print(cmd.get_my_sub_group_address_handle_list())

            self.device.set_my_sub_group_list(cmd.get_my_sub_group_list())
            self.device.set_my_sub_group_address_handle_list(cmd.get_my_sub_group_address_handle_list())
        else:
            for handle_address in cmd.get_my_sub_group_address_handle_list():
                print("AddrSubscriptionRemove:"+str(handle_address))
                self.device.send(cmd.AddrSubscriptionRemove(handle_address))
                time.sleep(0.5)
                # self.device.send(cmd.AddrGetAll())
            # result_groups = self.getGroupList()
            # for group in result_groups:
            #     group_address = group['id']
            #     print("AddrSubscriptionRemove:"+str(group_address))
            #     self.device.send(cmd.AddrSubscriptionRemove(group_address))
            #     time.sleep(0.5)

            cmd.init_my_sub_group_list()
            self.device.set_my_sub_group_list(cmd.get_my_sub_group_list())
            self.device.set_my_sub_group_address_handle_list(cmd.get_my_sub_group_address_handle_list())

    def doClose(self):
        if self.device is not None:
            self.device.close()
        self.device = None

    def getNodeByUnicastAddress(self, unicast_address):
        tList = [x for x in self.db.nodes if x.unicast_address.real == unicast_address]
        return tList[0] if len(tList) > 0 else None

    def getGroupByAddress(self, address):
        tList = [x for x in self.db.groups if x.address.real == address]
        return tList[0] if len(tList) > 0 else None


    def getConfigurationClient_heartbeat_subscription_set(self,light_id, src, dst, period):
        # if self.cc == None:
        cc = self.getConfigurationClient()
        address_handle = self.getAddressHandle(light_id)
        print("getConfigurationClient_heartbeat_subscription_set address_handle:"+str(address_handle))
        devkey_handle = self.getDevkeyHandle(light_id)
        print("getConfigurationClient_heartbeat_subscription_get devkey_handle:"+str(devkey_handle))
        cc.publish_set(devkey_handle, address_handle)
        cc.heartbeat_subscription_set(src, dst, period)

    def getConfigurationClient_heartbeat_subscription_get(self,light_id):
        # if self.cc == None:
        cc = self.getConfigurationClient()
        address_handle = self.getAddressHandle(light_id)
        print("getConfigurationClient_heartbeat_subscription_get address_handle:"+str(address_handle))
        devkey_handle = self.getDevkeyHandle(light_id)
        print("getConfigurationClient_heartbeat_subscription_get devkey_handle:"+str(devkey_handle))
        cc.publish_set(devkey_handle, address_handle )
        cc.heartbeat_subscription_get()


    def getConfigurationClient_heartbeat_publication_set2(self,light_id, dst, period):
        cc = self.getConfigurationClient()
        address_handle = self.getAddressHandle(light_id)
        devkey_handle = self.getDevkeyHandle(light_id)
        print("getConfigurationClient_heartbeat_publication_set2 address_handle:"+str(address_handle))
        print("getConfigurationClient_heartbeat_publication_set2 devkey_handle:"+str(devkey_handle))
        cc.publish_set(devkey_handle, address_handle)
        cc.heartbeat_publication_set2(dst, period)

    def getConfigurationClient_heartbeat_publication_get(self, light_id):
        cc = self.getConfigurationClient()
        address_handle = self.getAddressHandle(light_id)
        devkey_handle = self.getDevkeyHandle(light_id)
        print("getConfigurationClient_heartbeat_publication_get address_handle:"+str(address_handle))
        print("getConfigurationClient_heartbeat_publication_get devkey_handle:"+str(devkey_handle))
        cc.publish_set(devkey_handle, address_handle)
        cc.heartbeat_publication_get()

    def getVendorModelMessageClient(self):
        if self.vmm == None:
            self.vmm = VendorModelMessageClient()
            self.device.model_add(self.vmm)
        return self.vmm

    def getGenericOnOffFlashClient(self):
        if self.gcf == None:
            self.gcf = GenericOnOffFlashClient()
            self.device.model_add(self.gcf)
        return self.gcf

    def getGenericOnOffClient(self):
        if self.gc == None:
            self.gc = GenericOnOffClient()
            self.device.model_add(self.gc)
        return self.gc

    def getConfigurationClient(self):
        if self.cc == None:
            self.cc = ConfigurationClient(self.db)
            self.device.model_add(self.cc)
        return self.cc

    def getGenericLevelClient(self):
        if self.glc == None:
            self.glc = GenericLevelClient()
            self.device.model_add(self.glc)
        return self.glc

    def getSceneClient(self):
        if self.sc == None:
            self.sc = SceneClient()
            self.device.model_add(self.sc)
        return self.sc

    def getSensorClient(self):
        if self.src == None:
            self.src = SensorClient()
            self.device.model_add(self.src)
        return self.src

    def getSchedulerClient(self):
        if self.sdc == None:
            self.sdc = SchedulerClient()
            self.device.model_add(self.sdc)
        return self.sdc

    def getTimeClient(self):
        if self.tc == None:
            self.tc = TimeClient()
            self.device.model_add(self.tc)
        return self.tc

    def getLsbuClient(self):
        if self.lc == None:
            self.lc = LsbuClient()
            self.device.model_add(self.lc)

            self.lc.set_callback_energy_log(self.callback_energy_log)
        return self.lc

    def clearRespData(self, data_keys, model):
        for akey in data_keys:
            model.last_cmd_resp_dict[akey] = None

    def getRespData(self, data_keys, model, wait_time):

        """
            data_keys : is array
            wait_time : is integer
        """
        result_dict = {}

        for akey in data_keys:
            run_time = 0
            while (run_time < wait_time):
                # print("run_time:"+str(run_time)+" akey:"+str(akey))
                if model.last_cmd_resp_dict.get(akey) is not None:
                    result_dict[akey] = model.last_cmd_resp_dict.get(akey)
                    break
                time.sleep(0.4)
                run_time += 0.2

        return result_dict

    def deleteAllSchedule(self):
        self.dataDao.deleteAllSchedule()

    def searchData(self, id, light_type):
        return self.dataDao.getLight(id, light_type)

    def removeDevkeyHandle(self, devkey_handle=-1):

        if devkey_handle == -1:
            for i in range(DeviceService.MIN_DEVKEY_HANDLE_ID, DeviceService.MAX_DEVKEY_HANDLE_ID + 1):
                self.device.send(cmd.DevkeyDelete(i))
                time.sleep(0.2)
        else:
            self.device.send(cmd.DevkeyDelete(devkey_handle))
            time.sleep(0.2)
            if devkey_handle == self.last_devkey_handle:
                self.last_devkey_handle = None
                self.last_devkey_handle_id = None

    def removeAddressHandle(self, address_handle=-1):

        if address_handle == -1:
            data_key_ary = [RespOpcode.RESP_ADDR_GET_ALL]

            self.clearRespData(data_key_ary, self.provisioning)

            self.provisioning.last_cmd_resp_dict[RespOpcode.RESP_ADDR_GET_ALL] = None

            self.device.send(cmd.AddrGetAll())

            result_addr_get_all_data = self.getRespData(data_key_ary, self.provisioning, 2)

            if result_addr_get_all_data.get(data_key_ary[0]) is not None:
                for handle_address in result_addr_get_all_data.get(data_key_ary[0])[::2]:
                    self.device.send(cmd.AddrPublicationRemove(handle_address))
                    time.sleep(0.2)
                    self.device.send(cmd.AddrGetAll())

        else:
            self.device.send(cmd.AddrPublicationRemove(address_handle))
            time.sleep(0.2)
            self.device.send(cmd.AddrGetAll())

    def getDevkeyHandle(self, id, reTry=2):
        """
            id : is unicast_address by element[0]
                can't get unicast_address + n for elemnet[> 0]
        """
        if self.last_devkey_handle_id == id:
            return self.last_devkey_handle

        if self.last_devkey_handle is not None:
            self.removeDevkeyHandle(self.last_devkey_handle)

        data_key_ary = [RespOpcode.PROVISION_RESP_DEV_HANDLE_CODE]

        node_obj = self.getNodeByUnicastAddress(id)

        for i in range(0, reTry):
            try:
                self.clearRespData(data_key_ary, self.provisioning)
                self.device.send(cmd.DevkeyAdd(node_obj.unicast_address, 0, node_obj.device_key))
                result_data = self.getRespData(data_key_ary, self.provisioning, 3)
                a_data = result_data.get(data_key_ary[0])
                if a_data is not None:
                    self.last_devkey_handle = a_data[0] if len(a_data) > 0 else None
                    break
            except Exception as e:
                print(e)
                traceback.print_exc()

        if self.last_devkey_handle == None:
            self.last_devkey_handle_id = None
            raise Exception('fail to get devkey_handle')

        self.last_devkey_handle_id = id

        return self.last_devkey_handle

    def getAddressHandle(self, id, reTry=2):
        self.lock.acquire()
        try:
            if self.last_address_handle_id == id:
                return self.last_address_handle

            temp_last_address_handle = self.last_address_handle
            self.last_address_handle = None
            self.last_address_handle_id = None

            data_key_ary = [RespOpcode.PROVISION_RESP_ADDRESS_HANDLE_CODE]

            for i in range(0, reTry):
                try:
                    self.clearRespData(data_key_ary, self.provisioning)
                    self.device.send(cmd.AddrPublicationAdd(id))
                    result_data = self.getRespData(data_key_ary, self.provisioning, 3)
                    self.last_address_handle = result_data.get(data_key_ary[0])[0]
                    break
                except Exception as e:
                    print(e)
                    traceback.print_exc()

            if temp_last_address_handle is not None \
                    and temp_last_address_handle != self.last_address_handle:
                self.removeAddressHandle(temp_last_address_handle)

            if self.last_address_handle == None:
                self.last_address_handle_id = -1
                raise Exception('fail to get address_handle')

            self.last_address_handle_id = id
        finally:
            self.lock.release()
        return self.last_address_handle

    def model_add(self, v1, v2, v3, func_type=1, repeat=3):
        """
            func_type = DeviceService.TYPE_SINGLE_LIGHT, DeviceService.TYPE_GROUP
        """
        cc = self.getConfigurationClient()

        result_data = None
        for i in range(0, repeat):
            try:
                result_data = None
                if func_type == DeviceService.TYPE_SINGLE_LIGHT:
                    data_key_ary = [ConfigurationClient._MODEL_APP_STATUS.opcode]
                    self.clearRespData(data_key_ary, self.cc)

                    cc.model_app_bind(v1, v2, mt.ModelId(v3))

                    result_data = self.getRespData(data_key_ary, cc, 3)
                    if result_data[data_key_ary[0]] is not None:
                        if result_data[data_key_ary[0]] == AccessStatus.SUCCESS:
                            return None
                        break
                    else:
                        result_data = None
                elif func_type == DeviceService.TYPE_GROUP:
                    data_key_ary = [ConfigurationClient._MODEL_SUBSCRIPTION_STATUS.opcode]
                    self.clearRespData(data_key_ary, self.cc)

                    cc.model_subscription_add(v1, v2, mt.ModelId(v3))

                    result_data = self.getRespData(data_key_ary, cc, 3)
                    if result_data[data_key_ary[0]] is not None:
                        if result_data[data_key_ary[0]] == AccessStatus.SUCCESS:
                            return None
                        break
                    else:
                        result_data = None
            except:
                pass

    def model_publication_set(self, light_id, v2, v3):
        cc = self.getConfigurationClient()
        cc.model_publication_set(light_id, mt.ModelId(v2), mt.Publish(v3, index=0, ttl=4))
        time.sleep(1)

    def model_publication_set_with_RX(self, light_id, v2, v3):
        cc = self.getConfigurationClient()

        v2_hex = str(hex(v2))
        has_v2 = v2_hex in cc.last_cmd_resp_dict
        if has_v2:
            del cc.last_cmd_resp_dict[v2_hex]
        cc.model_publication_set(light_id, mt.ModelId(v2), mt.Publish(v3, index=0, ttl=4))
        # time.sleep(1)
        result_data = self.getRespData([v2_hex], cc, 10)
        print("model_publication_set_with_RX v2_hex:"+str(v2_hex))
        print("model_publication_set_with_RX result_data:"+str(result_data))
        if v2_hex in result_data and result_data[v2_hex] == AccessStatus.SUCCESS:
            return True
        return False


    def ccPublishSet(self, light_id):
        cc = self.getConfigurationClient()
        address_handle = self.getAddressHandle(light_id)
        devkey_handle = self.getDevkeyHandle(light_id)
        cc.publish_set(devkey_handle, address_handle)

    def light_group_remove(self, v1, v2, v3, repeat=3):
        """
        """
        cc = self.getConfigurationClient()

        result_data = None
        for i in range(0, repeat):
            try:
                result_data = None

                data_key_ary = [ConfigurationClient._MODEL_SUBSCRIPTION_STATUS.opcode]
                self.clearRespData(data_key_ary, self.cc)

                cc.model_subscription_delete(v1, v2, mt.ModelId(v3))

                result_data = self.getRespData(data_key_ary, cc, 3)
                if result_data[data_key_ary[0]] is not None:
                    if result_data[data_key_ary[0]] == AccessStatus.SUCCESS:
                        return None
                    break
                else:
                    result_data = None
            except:
                pass

    def getLightIdAry(self, light_id):
        result = [light_id, None]

        light_data = self.dataDao.getLight(light_id, DeviceService.TYPE_SINGLE_LIGHT)
        if (light_data is not None and light_data["is_temperature"] == 1):
            result[1] = light_id + 1
        return result

    def getGroupIdAry(self, group_id):
        result = [group_id, None]

        group_obj = self.getGroupByAddress(group_id)
        if group_obj is not None:
            result[1] = group_obj.sub_group1
        return result

    def getMeshInfo(self):
        meshUUID = ''.join('%02x' % x2 for x2 in self.db.mesh_UUID)
        meshUUID_str = uuid_tool.UUID(str(meshUUID))

        meshName = self.db.mesh_name
        netKey = self.db.net_keys[0]
        # print("getMeshInfo meshUUID:"+str(meshUUID_str))
        # print("getMeshInfo meshName:"+str(meshName))
        # print("getMeshInfo netKey:"+str(netKey))
        provisionerAddress = ""
        provisionerUUID_str = ""
        for pv_data in self.db.provisioners:
            provisionerAddress = '%04x' % (self.device.DEFAULT_LOCAL_UNICAST_ADDRESS_START)
            provisionerUUID = "".join(['%02x' % x for x in pv_data.UUID])
            provisionerUUID_str = uuid_tool.UUID(str(provisionerUUID))
            # print("getMeshInfo provisionerAddress:" + str(provisionerAddress))
            # print("getMeshInfo provisionerUUID:" + str(provisionerUUID_str))

        last_node = self.db.nodes[len(self.db.nodes) - 1]

        currentAddress = last_node.unicast_address
        elementCount = len(last_node.elements)

        tmpCurrentAddress = currentAddress
        if ((currentAddress % 4) > 0) :
            tmpCurrentAddress = currentAddress - (currentAddress % 4) + 4

        if ((elementCount % 4) > 0) :
            addCount = elementCount - (elementCount % 4) + 4
        else :
            addCount = elementCount
         # print("getMeshInfo last_node:" + str(last_node))
        nextUnicast = '%04x' % (tmpCurrentAddress + addCount)
        # print("getMeshInfo nextUnicast:"+str(nextUnicast))
        result = {
            "provisionerAddress": str(provisionerAddress),
            "provisionerUUID": str(provisionerUUID_str),
            "meshUUID": str(meshUUID_str),
            "nextUnicast": str(nextUnicast),
            "netKey": str(netKey),
            "meshName": str(meshName)
        }
        return result


    def scanDevice(self, is_clear, scan_time=3):

        result_list = []

        self.provisioning.scan_start()

        time.sleep(7)
        try:
            for x1 in self.provisioning.unprov_list:
                # print("self.provisioning.unprov_list x1:" + str(x1))
                print("self.provisioning.unprov_map :" + str(self.provisioning.unprov_map ))

                a_data = {}
                uuid = ''.join('%02x' % x2 for x2 in x1)
                print("self.provisioning.unprov_map.get(uuid):" + str(self.provisioning.unprov_map.get(uuid)))
                f_uuid = uuid_tool.UUID(str(uuid))
                adv_addr = self.provisioning.unprov_map.get(uuid).get('adv_addr')
                deviceAddress = ':'.join('%02x' % x2 for x2 in (adv_addr[::-1]))
                a_data['deviceDescription'] = ""
                a_data['rssi'] = self.provisioning.unprov_map.get(uuid).get('rssi')
                a_data['uuid'] = str(f_uuid)
                a_data['meshState'] = 0
                a_data['sensorClientGroupAddress'] = 0
                a_data['defaultName'] = "NoDefaultName"
                a_data['deviceAddress'] = deviceAddress.upper()

                result_list.append(a_data)
        finally:
            self.provisioning.scan_stop()

        return result_list

    def flashSingleLight(self, uuid):
        if self.is_busy:
            raise Exception("busy")
        try:
            str_uuid = uuid_tool.UUID(uuid).hex
            print("str_uuid:"+str_uuid)
            self.provisioning.scan_stop()
            self.provisioning.provision(uuid=str_uuid, attention_duration_s=10 )
        finally:
            self.is_busy = False

    def dongleReset(self):
        self.doClose()
        time.sleep(2)
        self.doInitDivice()
        time.sleep(5)

        device_uni_address = []
        for a_node in self.db.nodes:
            device_uni_address.append(a_node.unicast_address.real)

        self.deleteSingleLight(device_uni_address)
        time.sleep(1)

        self.device.send(cmd.StateClear())
        self.device.send(cmd.RadioReset())
        self.db.nodes.clear()
        self.db.groups.clear()
        self.db.deviceInfo.clear()
        self.db.groupInfo.clear()
        self.db.groupDetail.clear()
        self.db.sceneMain.clear()
        self.db.sceneGroupDetail.clear()
        self.db.sceneSingleDetail.clear()
        self.db.sceneSchedule.clear()
        self.db.sceneScheduleDetail.clear()
        self.db.store()
        self.dataDao.clearAll()

        shutil.rmtree(DeviceService.IMG_PATH, ignore_errors=True)

    def exportFile(self):

        tmp_folder_name = "zip"
        zip_folder = DeviceService.os_path + "/../" + tmp_folder_name
        if not os.path.exists(zip_folder):
            os.makedirs(zip_folder)
        else:
            shutil.rmtree(zip_folder, ignore_errors=True)
            os.makedirs(zip_folder)

        shutil.copyfile(DeviceService.database_path, zip_folder + "/example_database.json")
        shutil.copyfile("lights.db", zip_folder + "/lights.db")

        export_file = DeviceService.os_path + "/../export"

        if os.path.exists(export_file + ".zip"):
            os.remove(export_file + ".zip")

        shutil.make_archive(export_file, 'zip', zip_folder)

        export_info = {
            "folder": DeviceService.os_path + "/../",
            "file_name": "export.zip"
        }

        return export_info

    def exportJson(self):
        result_json = {"MeshInfo": {},
                       "provisionedData": {},
                       "groupInfoData": [],
                       "groupChildNodeData": [],
                       "deviceInfoData": [],
                       "sceneMainData": [],
                       "sceneGroupDetailData": [],
                       "sceneSingleDetailData": [],
                       "sceneScheduleData": [],
                       "sceneScheduleDetailData": []
                       }

        last_node = self.db.nodes[len(self.db.nodes) - 1]

        provisionedData = result_json["provisionedData"]
        provisionedData["$schema"] = "http://json-schema.org/draft-04/schema#"
        provisionedData["id"] = "TBD"
        provisionedData["version"] = "1.0"
        provisionedData["meshUUID"] = ''.join('%02x' % x2 for x2 in self.db.mesh_UUID)
        provisionedData["meshName"] = self.db.mesh_name
        provisionedData["nextUnicast"] = '%02x' % last_node.unicast_address + len(last_node.elements)
        provisionedData["timestamp"] = '%x' % int(datetime.now().timestamp())

        provisionedData["provisioners"] = []
        for pv_data in self.db.provisioners:
            t_data = {
                "provisionerName": pv_data.name,
                "provisionerAddress": '%04x' % (self.device.DEFAULT_LOCAL_UNICAST_ADDRESS_START),
                "UUID": "".join(['%02x' % x for x in pv_data.UUID]),
                "allocatedGroupRange": [{"lowAddress": '%04x' % x.low_address, "highAddress": '%04x' % x.high_address}
                                        for x in pv_data.allocated_group_range],
                "allocatedUnicastRange": [{"lowAddress": '%04x' % x.low_address, "highAddress": '%04x' % x.high_address}
                                          for x in pv_data.allocated_unicast_range],
            }
            provisionedData["provisioners"].append(t_data)

        provisionedData["netKeys"] = []
        for nkey_data in self.db.net_keys:
            t_data = {
                "name": nkey_data.name,
                "index": nkey_data.index,
                "key": "".join(['%02x' % x for x in nkey_data.key]),
                "phase": nkey_data.phase.real,
                "minSecurity": nkey_data.min_security.value,
                "timestamp": "0"
            }
            provisionedData["netKeys"].append(t_data)

        provisionedData["appKeys"] = []
        for akey_data in self.db.app_keys:
            t_data = {
                "name": akey_data.name,
                "index": akey_data.index,
                "boundNetKey": akey_data.bound_net_key,
                "key": "".join(['%02x' % x for x in akey_data.key])
            }
            provisionedData["appKeys"].append(t_data)

        provisionedData["nodes"] = []

        for a_node in self.db.nodes:
            t_data = {
                "UUID": "".join(['%02x' % x for x in a_node.UUID]),
                "deviceKey": "".join(['%02x' % x for x in a_node.device_key]),
                "unicastAddress": str(a_node.unicast_address),
                "security": a_node.security.value,
                "netKeys": [{'index': x.index} for x in a_node.net_keys],
                "configComplete": a_node.config_complete,
                "name": a_node.name,
                "cid": str(a_node.cid),
                "pid": str(a_node.pid),
                "vid": str(a_node.vid),
                "crpl": str(a_node.crpl),
                "features": {
                    "friend": a_node.features.friend,
                    "lowPower": a_node.features.low_power,
                    "proxy": a_node.features.proxy,
                    "relay": a_node.features.relay
                } if a_node.features is not None else {},
                "ttl": 0,
                "appKeys": [{"index": '%04x' % x.real} for x in a_node.app_keys],
                "blacklisted": False,
                "elements": [
                    {"index": x.index,
                     "location": x.location.to_json(),
                     "models": [
                         {
                             "modelId": x2.model_id.to_json(),
                             "subscribe": [x3.to_json() for x3 in x2.subscribe],
                         }
                         for x2 in x.models],
                     } for x in a_node.elements
                ],
            }
        return result_json

    def getSingleLightData(self, id):
        light_data = self.dataDao.getLight(id, DeviceService.TYPE_SINGLE_LIGHT)

        if light_data == None:
            raise Exception('light_data not exist')

        return light_data

    def getDeviceInfoData(self, address):
        for a_device in self.db.deviceInfo:
            if a_device.unicast_address == address:
                return a_device
        return None

    def updateDeviceInfo(self, device):
        for index, x in enumerate(self.db.deviceInfo):
            if x.unicast_address == device.unicast_address:
                self.db.deviceInfo[index] = device
                self.db.store()
                break

    def getDeviceId(self):
        ids = []
        for a_device in self.db.deviceInfo:
            ids.append(a_device.id)
        if not ids:
            return 1
        else:
            return max(ids) + 1

    def getGroupInfoData(self, address):
        for a_group in self.db.groupInfo:
            if a_group.unicast_address == address:
                return a_group

    def getGroupInfoDataByid(self, id):
        for a_group in self.db.groupInfo:
            if a_group.id == id:
                return a_group

    def updateGroupInfo(self, group):
        for index, x in enumerate(self.db.groupInfo):
            if x.unicast_address == group.unicast_address:
                self.db.groupInfo[index] = group
                self.db.store()
                break

    def getGroupInfoId(self):
        ids = []
        for a_group in self.db.groupInfo:
            ids.append(a_group.id)
        if not ids:
            return 1
        else:
            return max(ids) + 1

    def getGroupDetailId(self):
        ids = []
        for a_group_detail in self.db.groupDetail:
            ids.append(a_group_detail.id)
        if not ids:
            return 1
        else:
            return max(ids) + 1

    def getGroupInfoById(self, id):
        for group in self.db.groupInfo:
            if group.id == int(id):
                return group

    def getGroupInfoByAddress(self, address):
        for group in self.db.groupInfo:
            if group.unicast_address == int(address):
                return group

    def getGroupDetailByGroupId(self, group_id):
        group_detail = []
        for gdetail in self.db.groupDetail:
            if gdetail.group_ID == group_id:
                group_detail.append(gdetail)
        return group_detail

    def getGroupDetailByGroupIdAndDeviceAddress(self, group_id, device_address):
        for gdetail in self.db.groupDetail:
            if gdetail.group_ID == group_id and gdetail.unicast_address == device_address:
                return gdetail

    def getSceneGroupDetail(self, group_address):
        for sgdIdx in range(0, len(self.db.sceneGroupDetail)):
            if self.db.sceneGroupDetail[sgdIdx].group_address == group_address:
                return self.db.sceneGroupDetail[sgdIdx]

    def getSceneMainForSceneId(self, id):
        for smIdx in range(0, len(self.db.sceneMain)):
            if self.db.sceneMain[smIdx].id == id:
                return self.db.sceneMain[smIdx]

    def getSceneMainForSceneNum(self, scene_num):
        for smIdx in range(0, len(self.db.sceneMain)):
            if self.db.sceneMain[smIdx].scene_num == scene_num:
                return self.db.sceneMain[smIdx]

    def getSceneScheduleForId(self, id):
        for ssIdx in range(0, len(self.db.sceneSchedule)):
            if self.db.sceneSchedule[ssIdx].id == id:
                return self.db.sceneSchedule[ssIdx]

    def getSceneScheduleDetailId(self):
        ids = []
        for a_scene_schedule_detail in self.db.sceneScheduleDetail:
            ids.append(a_scene_schedule_detail.id)
        if not ids:
            return 1
        else:
            return max(ids) + 1

    def updateSingleLight(self, id, name, img_file):
        a_node = self.getNodeByUnicastAddress(id)
        light_data = self.dataDao.getLight(id, DeviceService.TYPE_SINGLE_LIGHT)

        if img_file is not None:
            if light_data["img_path"] is not None:
                os.remove(DeviceService.IMG_PATH + light_data["img_path"])

            image_name = "L_" + str(datetime.now().timestamp())
            img_file.save(DeviceService.IMG_PATH + image_name)

            self.dataDao.updateLightImage(id, DeviceService.TYPE_SINGLE_LIGHT, image_name)
        a_node.name = name
        self.db.store()


    def getSingleLightSensor_descriptorGet(self, uniAddress):
        address_handle = self.getAddressHandle(uniAddress)
        device = self.getDeviceInfoData(uniAddress)
        if device is not None:
            sc = self.getSensorClient()
            sc.publish_set(0, address_handle)
            #下方指令可查出 data:['51', '4d', '00', '00', '00', '00', '00', '00', '00', '4f', '00', '00', '00', '00', '00', '00', '00', 'f0', '00', '00', '00', '00', '00', '00', '00']
            # sc.descriptorGet(propertyID=0)
            #下方指令可查出 data:['51', 'f0', '00', '00', '00', '00', '00', '00', '00']
            # sc.descriptorGet(propertyID=240)
            sc.last_cmd_resp_dict = {}
            result_data = {}
            retry_i = 0
            while 0 not in result_data and retry_i < 3 :
                retry_i += 1
                sc.descriptorGet(propertyID=0)
                result_data = self.getRespData([0], sc, 3)
                if gl.get_value('MORE_LOG'):
                    print("result_data:"+str(result_data))

            if 0 in result_data :
                return result_data[0]
        return []

    def getSingleLightSensor_cadenceGet(self, uniAddress,propertyID):
        address_handle = self.getAddressHandle(uniAddress)
        device = self.getDeviceInfoData(uniAddress)
        if device is not None:
            sc = self.getSensorClient()
            sc.publish_set(0, address_handle)
            #下方指令可查出 data:['57', '4d', '00', '00', '00', '00', '00', '00', '00']
            # sc.cadenceGet(propertyID=77)
            #下方指令可查出 data:['57', '4f', '00', '01', '03', '00', '01', '00', '02']
            # sc.cadenceGet(propertyID=79)
            #下方指令可查出 data:['57', 'f0', '00', '00', '00', '00', '00', '00', '00', '00', '00', '00', '00']
            #Sensor Cadence Status:propertyID:240 periodDivisor:0 triggerType:0 triggerDeltaDown:0 triggerDeltaUp:0 minInterval:0 fastCadenceLow:0 fastCadenceHigh:0
            # sc.cadenceGet(propertyID=240)
            sc.last_cmd_resp_dict = {}
            result_data = {}
            retry_i = 0
            while propertyID not in result_data and retry_i < 3 :
                retry_i += 1
                sc.cadenceGet(propertyID=propertyID)
                result_data = self.getRespData([propertyID], sc, 3)
                if gl.get_value('MORE_LOG'):
                    print("result_data:"+str(result_data))

            if propertyID in result_data :
                return result_data[propertyID]

        return []


    def getSingleLightSensor_cadenceSet(self, uniAddress,propertyID,periodDivisor, triggerType, triggerDeltaDown, triggerDeltaUp, minInterval, low, high):
        address_handle = self.getAddressHandle(uniAddress)
        device = self.getDeviceInfoData(uniAddress)
        if device is not None:
            sc = self.getSensorClient()
            sc.publish_set(0, address_handle)

            # sc.cadenceSet(propertyID=79, periodDivisor=1, triggerType=0, triggerDeltaDown=1, triggerDeltaUp=2, minInterval=3, low=4, high=5, ack=True, repeat=1)
            #            data:['57', '4f', '00', '01', '01', '00', '02', '00', '03', '04', '00', '05', '00']

            # sc.cadenceSet(propertyID=240, periodDivisor=1, triggerType=0, triggerDeltaDown=1, triggerDeltaUp=2, minInterval=3, low=4, high=5, ack=True, repeat=1)
            #            data:['57', 'f0', '00', '01', '01', '00', '02', '00', '03', '04', '00', '05', '00']
            sc.last_cmd_resp_dict = {}
            result_data = {}
            retry_i = 0
            while propertyID not in result_data and retry_i < 3 :
                retry_i += 1
                sc.cadenceSet(propertyID=propertyID, periodDivisor=1, triggerType=0, triggerDeltaDown=1, triggerDeltaUp=2, minInterval=3, low=4, high=5, ack=True, repeat=1)
                result_data = self.getRespData([propertyID], sc, 5)
                if gl.get_value('MORE_LOG'):
                    print("result_data:"+str(result_data))

            if propertyID in result_data :
                return result_data[propertyID]

        return []

    def getSingleLightSensor_settingsGet(self, uniAddress,propertyID):
        address_handle = self.getAddressHandle(uniAddress)
        device = self.getDeviceInfoData(uniAddress)
        if device is not None:
            sc = self.getSensorClient()
            sc.publish_set(0, address_handle)

            #下方指令可查出 data:['58', 'f0', '00', '11', '00', '12', '00', '13', '00', '14', '00', '15', '00', '16', '00', '17', '00', '18', '00', '19', '00']
            sc.last_cmd_resp_dict = {}
            result_data = {}
            retry_i = 0
            while propertyID not in result_data and retry_i < 3 :
                retry_i += 1
                sc.settingsGet(propertyID=propertyID)
                result_data = self.getRespData([propertyID], sc, 10)
                if gl.get_value('MORE_LOG'):
                    print("result_data:"+str(result_data))

            if propertyID in result_data :
                return result_data[propertyID]

        return []

    def getSingleLightSensor_settingGet(self, uniAddress,propertyID,settingPropertyID):
        address_handle = self.getAddressHandle(uniAddress)
        device = self.getDeviceInfoData(uniAddress)
        if device is not None:
            sc = self.getSensorClient()
            sc.publish_set(0, address_handle)

            sc.last_cmd_resp_dict = {}
            result_data = {}
            retry_i = 0
            tmp_key = str(propertyID)+"."+str(settingPropertyID)
            if gl.get_value('MORE_LOG'):
                print("getSingleLightSensor_settingGet:tmp_key:"+tmp_key)
            while tmp_key not in result_data and retry_i < 3 :
                retry_i += 1
                sc.settingGet(propertyID=propertyID,settingPropertyID=settingPropertyID)
                result_data = self.getRespData([tmp_key], sc, 3)
                if gl.get_value('MORE_LOG'):
                    print("result_data:"+str(result_data))

            if tmp_key in result_data :
                return result_data[tmp_key]

        return []


    def getSingleLightSensor_settingSet(self, uniAddress,propertyID,settingPropertyID,settingValue):
        address_handle = self.getAddressHandle(uniAddress)
        device = self.getDeviceInfoData(uniAddress)
        if device is not None:
            sc = self.getSensorClient()
            sc.publish_set(0, address_handle)

            sc.last_cmd_resp_dict = {}
            result_data = {}
            retry_i = 0
            tmp_key = str(propertyID)+"."+str(settingPropertyID)
            if gl.get_value('MORE_LOG'):
                print("getSingleLightSensor_settingSet:tmp_key:"+tmp_key)
            while tmp_key not in result_data and retry_i < 3 :
                retry_i += 1
                sc.settingSet(propertyID=propertyID,settingPropertyID=settingPropertyID,settingValue=settingValue)
                result_data = self.getRespData([tmp_key], sc, 3)
                if gl.get_value('MORE_LOG'):
                    print("result_data:"+str(result_data))

            if tmp_key in result_data :
                return result_data[tmp_key]

        return []

    def getSingleLightSensor_Publish(self, uniAddress, enable, publishType, publishUniAddress):

        device = self.getDeviceInfoData(uniAddress)
        a_node = self.getNodeByUnicastAddress(uniAddress)
        if device is not None and a_node is not None:
            if publishUniAddress == -1:
                publishUniAddress = self.device.DEFAULT_LOCAL_UNICAST_ADDRESS_START
            if gl.get_value('MORE_LOG'):
                print("enable:" + str(enable))
                print("publishUniAddress:" + str(publishUniAddress))
            if enable == 0 :
                publishUniAddress = uniAddress

            self.ccPublishSet(uniAddress)
            self.model_add(a_node.unicast_address, 0, 0x1100)
            self.model_add(a_node.unicast_address, 0, 0x1101)
            self.model_add(a_node.unicast_address, publishUniAddress, 0x1100, publishType)
            self.model_add(a_node.unicast_address, publishUniAddress, 0x1101, publishType)
            result1 = self.model_publication_set_with_RX(a_node.unicast_address, 0x1100, publishUniAddress)
            result2 = self.model_publication_set_with_RX(a_node.unicast_address, 0x1101, publishUniAddress)
            if gl.get_value('MORE_LOG'):
                print("result1:" + str(result1))
                print("result2:" + str(result2))
            # sc.last_cmd_resp_dict = {}
            # sc.descriptorGet(propertyID=0)
            # result_data = self.getRespData([0], sc, 3)
            # if gl.get_value('MORE_LOG'):
            #     print("result_data:"+str(result_data))
            if result1 and result2:
                return True
        return False

    def getSingleLightOutput(self, id):
        address_handle = self.getAddressHandle(id)
        if address_handle is not None:
            vmm = self.getVendorModelMessageClient()
            vmm.publish_set(0, address_handle)
            vmm.last_cmd_resp_dict = {}
            result_data = {}
            retry_i = 0
            while id not in result_data and retry_i < 5 :
                retry_i += 1
                vmm.get()
                result_data = self.getRespData([id], vmm, 0.5)
                if gl.get_value('MORE_LOG'):
                    print("result_data:"+str(result_data))
            return result_data

        return None

    def setSingleLightOutput(self, id, output):
        address_handle = self.getAddressHandle(id)
        if address_handle is not None:
            vmm = self.getVendorModelMessageClient()
            vmm.publish_set(0, address_handle)
            vmm.last_cmd_resp_dict = {}
            result_data = {}
            retry_i = 0
            while id not in result_data and retry_i < 5 :
                retry_i += 1
                if output == "linear":
                    vmm.set(0x09)
                else:
                    vmm.set(0x01)
                result_data = self.getRespData([id], vmm, 1)
                if gl.get_value('MORE_LOG'):
                    print("result_data:"+str(result_data))
            return result_data

        return None


    def setGroupOutput(self, id, output):
        address_handle = self.getAddressHandle(id)
        if address_handle is not None:
            vmm = self.getVendorModelMessageClient()
            vmm.publish_set(0, address_handle)
            vmm.last_cmd_resp_dict = {}
            result_data = {}
            retry_i = 0
            while id not in result_data and retry_i < 5 :
                retry_i += 1
                if output == "linear":
                    vmm.set(0x09)
                else:
                    vmm.set(0x01)
                result_data = self.getRespData([id], vmm, 0.5)
                if gl.get_value('MORE_LOG'):
                    print("result_data:"+str(result_data))
            #Group不會有RX,所以直接回傳結果
            result_data[id] = output
            return result_data

        return None

    def setSingleLightOnOffFlash(self, id, blinkTimes):
        address_handle = self.getAddressHandle(id)
        device = self.getDeviceInfoData(id)
        if device is not None:
            gcf = self.getGenericOnOffFlashClient()
            gcf.publish_set(0, address_handle)
            gcf.set(blinkTimes,0x0A,0x00, ack=False, repeat=3)
        return device

    '''
    1. get handler of the device
    2. 從database取得裝置的資料
    3. 取得這個model的client端
    4. 設置廣播參數以及目標addr
    5. repeat廣播4.的設置3次
    6. 將剛剛取得最新的裝置資料存進去database
    '''
    def setSingleLightOnOff(self, id, on_off, transition_time, repeat, ack):
        address_handle = self.getAddressHandle(id)
        device = self.getDeviceInfoData(id)
        if device is not None:
            gc = self.getGenericOnOffClient()
            gc.publish_set(0, address_handle)
            gc.set(on_off, ack=ack, transition_time_ms=transition_time, repeat=repeat)
            if on_off:
                device.switch_state = 1
            else:
                device.switch_state = 0
            if testSaveDb:
                self.updateDeviceInfo(device)
        return device

    # gc.set(on_off)
    # gc.set(on_off)

    def setSingleLightLightness(self, id, lightness_per, transition_time, repeat, ack):
        """
            lightness :: -32767~32767
        """
        device = self.getDeviceInfoData(id)
        if device is not None:
            lightness = 0
            # if lightness_per > 50:
            #     lightness = int((lightness_per - 50) / 50 * 32767)
            #
            #     if lightness > 32767:
            #         lightness = 32767
            # else:
            #     lightness = int((50 - lightness_per) / 50 * -32767)
            #     if lightness < -32767:
            #         lightness = -32767

            lightness = int((lightness_per / 255) * 65535 - 32768)
            if lightness == -32768:
                lightness = -32767
            print("lightness:" + str(lightness))
            address_handle = self.getAddressHandle(id)
            glc = self.getGenericLevelClient()
            glc.publish_set(0, address_handle)
            glc.set(lightness, ack=ack, transition_time_ms=transition_time, repeat=repeat)
            device.dimming_value = lightness_per
            if testSaveDb:
                self.updateDeviceInfo(device)
        return device

    # glc.set(lightness)
    # glc.set(lightness)

    def setSingleLightTemperature(self, id, temperature_per, transition_time, repeat, ack):
        """
            temperature_per :: 0~ 100
            temperature :: -32767~32767
        """
        temperature = 0
        # if temperature_per > 50:
        #     temperature = int((temperature_per - 50) / 50 * 32767)
        #
        #     if temperature > 32767:
        #         temperature = 32767
        # else:
        #     temperature = int((50 - temperature_per) / 50 * -32767)
        #     if temperature < -32767:
        #         temperature = -32767
        device = self.getDeviceInfoData(id)
        if device is not None:
            temperature = int((temperature_per / 255) * 65535 - 32768)
            if temperature == -32768:
                temperature = -32767

            light_data = self.dataDao.getLight(id, DeviceService.TYPE_SINGLE_LIGHT)
            print("light_data:"+str(light_data))
            if light_data["is_temperature"] == 1:
                address_handle = self.getAddressHandle(id + 1)

                glc = self.getGenericLevelClient()
                glc.publish_set(0, address_handle)
                glc.set(temperature, ack=ack, transition_time_ms=transition_time, repeat=repeat)
                device.color_value = temperature_per
                if testSaveDb:
                    self.updateDeviceInfo(device)
        return device

    # glc.set(temperature)
    # glc.set(temperature)

    def addSingleLight(self, str_uuid, my_default_name):
        default_name = ""
        is_work_ok = False
        if self.is_busy:
            raise Exception("busy")

        try:
            self.is_busy = True
            self.provisioning.scan_stop()
            b_uuid = None
            str_uuid = uuid_tool.UUID(str_uuid).hex

            for a_node in self.db.nodes:
                if str_uuid == ''.join('%02x' % b for b in a_node.UUID).lower():
                    b_uuid = a_node.UUID
                    break
            if b_uuid is not None:
                raise Exception('uuid exist in db')

            data_key_ary_1 = ["Add Light Status", "Provision Node Address"]

            data_key_ary = [RespOpcode.PROVISION_RESP_DEV_HANDLE_CODE,
                            RespOpcode.PROVISION_RESP_ADDRESS_HANDLE_CODE]

            self.clearRespData(data_key_ary_1, self.provisioning)

            self.clearRespData(data_key_ary, self.provisioning)

            self.provisioning.provision(uuid=str_uuid)

            time.sleep(9)

            result_data = self.getRespData(data_key_ary_1, self.provisioning, 60)
            # print("result_data1:" + str(result_data))
            dev_handle = None
            address_handle = None

            result_data = self.getRespData(data_key_ary, self.provisioning, 3)
            # print("result_data2:" + str(result_data))

            dev_handle = result_data.get(data_key_ary[0])
            address_handle = result_data.get(data_key_ary[1])
            node_idx = len(self.db.nodes) - 1

            if dev_handle == None or len(dev_handle) <= 0:
                raise Exception('fail to get devkey_handle')

            unicast_address = self.db.nodes[node_idx].unicast_address
            print("unicast_address:" + str(unicast_address))

            cc = self.getConfigurationClient()
            config_data_key_ary = [cc._COMPOSITION_DATA_STATUS.opcode]
            cc.publish_set(dev_handle[0], address_handle[0])
            cc.appkey_add(0)

            time.sleep(15)
            cc.composition_data_get()




            result_data = self.getRespData(config_data_key_ary, cc, 30)

            config_data_state = result_data.get(config_data_key_ary[0])
            print("config_data_state:" + str(config_data_state))
            if config_data_state == AccessStatus.SUCCESS:
                self.dataDao.saveLight(unicast_address, DeviceService.TYPE_SINGLE_LIGHT, 0)

                self.last_address_handle = address_handle[0]
                self.last_address_handle_id = unicast_address
                self.last_devkey_handle = dev_handle[0]
                self.last_devkey_handle_id = unicast_address

                self.model_add(unicast_address, 0, 0x1000)
                self.model_add(unicast_address, 0, 0x1002)
                self.model_add(unicast_address, 0, 0x1204)
                self.model_add(unicast_address, 0, 0x1203)
                self.model_add(unicast_address, 0, 0x1206)
                self.model_add(unicast_address, 0, 0x1207)
                self.model_add(unicast_address, 0, 0x1200)
                self.model_add(unicast_address, 0, 0x1201)

                self.provisioning.unprov_list.clear()

                if my_default_name == "" :
                    product_map_key = str(cc.pid).upper() + "_" + str(cc.vid).upper()
                    print("product_map_key:" + product_map_key)
                    if product_map_key in self.product_maps:
                        print("self.product_maps[ product_map_key ]:" + self.product_maps[ product_map_key ])
                        default_name = self.product_maps[ product_map_key ]
                else:
                    default_name = my_default_name
                print("default_name:" + default_name)

                is_temperature = 0
                self.db.nodes[node_idx].name = default_name

                if len(self.db.nodes[node_idx].elements) > 1 \
                        and self.db.nodes[node_idx].elements[1].models is not None:
                    model_1002_ary = [x for x in self.db.nodes[node_idx].elements[1].models if
                                      x.model_id.model_id == int("1002", 16)]
                    if len(model_1002_ary) > 0:
                        self.model_add(unicast_address + 1, 0, 0x1002)
                        self.model_add(unicast_address + 1, 0, 0x1204)
                        self.model_add(unicast_address + 1, 0, 0x1203)
                        self.model_add(unicast_address + 1, 0, 0x1206)
                        self.model_add(unicast_address + 1, 0, 0x1207)
                        is_temperature = 1

                self.dataDao.updateLight(unicast_address, DeviceService.TYPE_SINGLE_LIGHT, is_temperature)

                f_uuid = uuid_tool.UUID(str_uuid)
                print("f_uuid:" + str(f_uuid))
                device_name = default_name + "_" + str(int(unicast_address / 4))
                device_id = self.getDeviceId()
                if gl.get_value('MORE_LOG'):
                    print("device_id:"+str(device_id))
                    print("device_name:"+str(device_name))
                    print("self.db.nodes[node_idx].name:"+str(self.db.nodes[node_idx].name))
                self.db.deviceInfo.append(
                    mt.DeviceInfo(id=device_id, name=device_name, default_name=self.db.nodes[node_idx].name,uuid=str(f_uuid),
                                  unicast_address=int(unicast_address),
                                  switch_state=1, upload_state=0, dimming_value=255, color_value=0))
                self.db.store()

                self.addC000Group(unicast_address)
                is_work_ok = True
        finally:
            self.is_busy = False

        if is_work_ok:
            self.removeDevkeyHandle(self.last_devkey_handle)
            return self.db.nodes[node_idx]
        else:
            del self.db.nodes[node_idx]
            self.db.store()
            return None

    def getDeviceInfoByUuid(self,uuid):
        deviceList = []
        for device in self.db.deviceInfo:
            if device.uuid == uuid:
                device = {
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
                deviceList.append(device)
                return deviceList
        return deviceList

    def getDeviceInfoByUniAddress(self,uniAddress):
        deviceList = []
        for device in self.db.deviceInfo:
            if device.unicast_address == int(uniAddress):
                device = {
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
                deviceList.append(device)
                return deviceList
        return deviceList

    def getDeviceInfoById(self,id):
        deviceList = []
        for device in self.db.deviceInfo:
            if device.id == int(id):
                device = {
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
                deviceList.append(device)
                return deviceList
        return deviceList

    def getDeviceInfoList(self):
        deviceList = []
        for device in self.db.deviceInfo:
            device = {
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
            deviceList.append(device)
        return deviceList

    def getLightList(self):
        a_list = []
        for x in self.db.nodes:
            device_data = self.getDeviceInfoData(x.unicast_address.real)
            light = {}
            light["id"] = x.unicast_address.real
            light["uniAddress"] = x.unicast_address.real
            light["name"] = x.name
            light["UUID"] = device_data.uuid
            light_data = self.dataDao.getLight(light["id"], DeviceService.TYPE_SINGLE_LIGHT)
            if light_data == None:
                continue

            light["image"] = light_data["img_path"]
            light["defaultName"] = device_data.default_name
            a_list.append(light)
        return a_list

    def getAllLightStatus(self):

        address_handle = self.getAddressHandle(DeviceService.ALL_GROUP_ID)

        gc = self.getGenericOnOffClient()
        gc.publish_set(0, address_handle)
        gc.data_key_ary = [id]
        gc.last_cmd_resp_dict = {}
        gc.get()
        time.sleep(5)

        light_status_map = {}

        for key, value in gc.last_cmd_resp_dict.items():
            status_map = None
            if light_status_map.get(key) is None:
                status_map = {"device_id": key}
            else:
                status_map = light_status_map[key]

            status_map["onOff"] = value
            light_status_map[key] = status_map

        glc = self.getGenericLevelClient()
        glc.publish_set(0, address_handle)
        glc.last_cmd_resp_dict = {}
        glc.get()
        time.sleep(5)

        for key, value in glc.last_cmd_resp_dict.items():
            status_map = None
            if light_status_map.get(key) is None:
                status_map = {"device_id": key}
            else:
                status_map = light_status_map[key]

            lightness = value
            lightness = int((lightness + 32767) * 100 / (32767 * 2))
            status_map["level1"] = lightness
            light_status_map[key] = status_map

        return light_status_map

    def getSingleLightOnOff(self, id):

        """
        """
        address_handle = self.getAddressHandle(id)

        retry = 5
        timeout = 3
        retrySleep = 0.05

        state = -1
        gc = self.getGenericOnOffClient()
        gc.publish_set(0, address_handle)

        data_key_ary = [str(id) + "onOff"]
        print("getSingleLight onOff:" + str(data_key_ary))
        self.clearRespData(data_key_ary, gc)

        for i in range(0, retry):
            try:
                gc.get()
                result_data = self.getRespData(data_key_ary, gc, timeout)
                if result_data != {}:
                    state = result_data.get(data_key_ary[0])
                    print("getSingleLight onOff ok:"+str(state))
                    break
                else:
                    time.sleep(retrySleep)
            except:
                pass

        result = {
            "status": "success",
            "code": 200,
            "message": "",
            "payload": {}
        }

        if state == -1:
            result["message"] = 'timeout'
        else:
            device = self.getDeviceInfoData(id)
            device.switch_state = state

            if testSaveDb:
                self.updateDeviceInfo(device)

            result["payload"] = {
                "devices": [
                    {
                        "id": device.id,
                        "name": device.name,
                        "uniAddress": device.unicast_address,
                        "uuid": device.uuid,
                        "state": {
                            "onOff": device.switch_state,
                        }
                    }
                ]
            }

        return result


    def getSingleLightLevel(self, id):

        """
        """

        address_handle = self.getAddressHandle(id)

        retry = 5
        timeout = 3
        retrySleep = 0.05

        lightness = -1
        glc = self.getGenericLevelClient()
        for i in range(0, retry):
            try:
                glc.publish_set(0, address_handle)

                data_key_ary3 = [str(id)+"level"]
                print("getSingleLight lightness:"+str(data_key_ary3))
                self.clearRespData(data_key_ary3, glc)
                glc.get()
                result_data3 = self.getRespData(data_key_ary3, glc, timeout)

                if result_data3 != {} :
                    lightness = result_data3[data_key_ary3[0]]

                    # 新計算法
                    lightness = int(255 * (lightness + 32768) / 65535)
                    print("getSingleLight lightness ok:"+str(lightness))
                    # print("liby temperature_per1:"+str(temperature_per))
                    # lightness = int((lightness + 32767) * 100 / (32767 * 2))
                    break
                else:
                    time.sleep(retrySleep)

            except:
                pass

        result = {
            "status": "success",
            "code": 200,
            "message": "",
            "payload": {}
        }

        if lightness == -1:
            result["message"] = 'timeout'
        else:
            device = self.getDeviceInfoData(id)
            device.dimming_value = lightness
            if testSaveDb:
                self.updateDeviceInfo(device)

            result["payload"] = {
                "devices": [
                    {
                        "id": device.id,
                        "name": device.name,
                        "uniAddress": device.unicast_address,
                        "uuid": device.uuid,
                        "state": {
                            "level": device.dimming_value,
                        }
                    }
                ]
            }

        return result

    def getSingleLightCct(self, id):

        """
        """


        retry = 5
        timeout = 3
        retrySleep = 0.05

        temperature = -1
        glc = self.getGenericLevelClient()
        for i in range(0, retry):
            try:

                address_handle = self.getAddressHandle(id + 1)
                glc.publish_set(0, address_handle)
                data_key_ary3 = [str(id + 1) + "level"]
                print("getSingleLight temperature:" + str(data_key_ary3))
                self.clearRespData(data_key_ary3, glc)
                glc.get()
                result_data3 = self.getRespData(data_key_ary3, glc, timeout)
                if result_data3 != {}:
                    temperature = result_data3[data_key_ary3[0]]

                    # 新計算法
                    temperature = int(255 * (temperature + 32768) / 65535)
                    print("getSingleLight temperature ok:" + str(temperature))
                    # print("liby temperature_per2:" + str(temperature_per))
                    # temperature = int((temperature + 32767) * 100 / (32767 * 2))
                    break
                else:
                    time.sleep(retrySleep)


            except:
                pass

        result = {
            "status": "success",
            "code": 200,
            "message": "",
            "payload": {}
        }

        if temperature == -1:
            result["message"] = 'timeout'
        else:
            device = self.getDeviceInfoData(id)
            device.color_value = temperature

            if testSaveDb:
                self.updateDeviceInfo(device)

            result["payload"] = {
                "devices": [
                    {
                        "id": device.id,
                        "name": device.name,
                        "uniAddress": device.unicast_address,
                        "uuid": device.uuid,
                        "state": {
                            "cct": device.color_value
                        }
                    }
                ]
            }

        return result

    def getSingleLight(self, id):

        """
        """
        light_data = self.getSingleLightData(id)

        address_handle = self.getAddressHandle(id)

        state = False
        flagOfstatus = False

        gc = self.getGenericOnOffClient()

        a_node = self.getNodeByUnicastAddress(id)
        retry = 5
        timeout = 3
        retrySleep = 0.1
        for i in range(0, retry):
            try:
                gc.publish_set(0, address_handle)

                data_key_ary = [str(id)+"onOff"]
                print("getSingleLight onOff:"+str(data_key_ary))
                self.clearRespData(data_key_ary, gc)

                gc.get()

                result_data = self.getRespData(data_key_ary, gc, timeout)

                if result_data != {} :
                    state = result_data.get(data_key_ary[0])
                    print("getSingleLight onOff ok:"+str(state))
                    flagOfstatus = True
                    break
                else:
                    time.sleep(retrySleep)
            except:
                pass


        if state is None:
            state = 0

        node_groups = [x.address.real for x in self.db.groups if id in x.nodes_unicast_address]

        lightness = 0

        glc = self.getGenericLevelClient()
        for i in range(0, retry):
            try:
                glc.publish_set(0, address_handle)

                data_key_ary3 = [str(id)+"level"]
                print("getSingleLight lightness:"+str(data_key_ary3))
                self.clearRespData(data_key_ary3, glc)
                glc.get()
                result_data3 = self.getRespData(data_key_ary3, glc, timeout)

                if result_data3 != {} :
                    lightness = result_data3[data_key_ary3[0]]

                    # 新計算法
                    lightness = int(255 * (lightness + 32768) / 65535)
                    print("getSingleLight lightness ok:"+str(lightness))
                    flagOfstatus = True and flagOfstatus
                    # print("liby temperature_per1:"+str(temperature_per))
                    # lightness = int((lightness + 32767) * 100 / (32767 * 2))
                    break
                else:
                    time.sleep(retrySleep)

            except:
                pass

        temperature = 0
        for i in range(0, retry):
            try:
                if light_data["is_temperature"] == 1:
                    data_key_ary3 = [str(id+1)+"level"]

                    address_handle = self.getAddressHandle(id + 1)

                    glc.publish_set(0, address_handle)
                    print("getSingleLight temperature:" + str(data_key_ary3))
                    self.clearRespData(data_key_ary3, glc)
                    glc.get()
                    result_data3 = self.getRespData(data_key_ary3, glc, timeout)
                    if result_data3 != {}:
                        temperature = result_data3[data_key_ary3[0]]

                        # 新計算法
                        temperature = int(255 * (temperature + 32768) / 65535)
                        print("getSingleLight temperature ok:" + str(temperature))
                        flagOfstatus = True and flagOfstatus
                        # print("liby temperature_per2:" + str(temperature_per))
                        # temperature = int((temperature + 32767) * 100 / (32767 * 2))
                        break
                    else:
                        time.sleep(retrySleep)

            except:
                pass

        return {'id': id,
                'name': a_node.name,
                'image': light_data["img_path"],
                'lightness': lightness,
                'temperature': temperature,
                'state': True if state > 0 else False,
                'is_temperature': True if light_data["is_temperature"] == 1 else False,
                'group': [x for x in self.db.groups if x.address.real in node_groups],
                'timeout': True if flagOfstatus == True else False}

    def deleteSingleLight(self, address_list):
        """
        """
        cc = self.getConfigurationClient()

        for id in address_list:
            light_data = self.dataDao.getLight(id, DeviceService.TYPE_SINGLE_LIGHT)
            if light_data is not None:

                try:
                    address_handle = self.getAddressHandle(id)
                    devkey_handle = self.getDevkeyHandle(id)
                    cc.publish_set(devkey_handle, address_handle)
                    cc.node_reset()

                    if light_data["img_path"] is not None:
                        os.remove(DeviceService.IMG_PATH + light_data["img_path"])
                except:
                    pass

            for a_group in self.db.groups:
                if id in a_group.nodes_unicast_address:
                    a_group.nodes_unicast_address.remove(id)

            for index, x in enumerate(self.db.nodes):
                if x.unicast_address.real == id:
                    del self.db.nodes[index]
                    break

            for index, x in enumerate(self.db.deviceInfo):
                if x.unicast_address == id:
                    del self.db.deviceInfo[index]
                    break

            for index, x in enumerate(self.db.groupDetail):
                if x.unicast_address == id:
                    del self.db.groupDetail[index]
                    break

            for index, x in enumerate(self.db.sceneSingleDetail):
                if x.single_address == id:
                    del self.db.sceneSingleDetail[index]
                    break

            for index, x in enumerate(self.db.sceneScheduleDetail):
                if x.single_address == id:
                    del self.db.sceneScheduleDetail[index]
                    break

            self.db.store()

            self.dataDao.deleteLight(id, DeviceService.TYPE_SINGLE_LIGHT)

    def getSingleLightSceneList(self, light_id):

        relation_list = self.dataDao.getLightSceneRelationList(light_id)

        result_list = []

        for a_data in relation_list:
            result_list.append({"id": a_data["scene_id"], "name": a_data["scene_name"]})

        return result_list

    def getSingleLightScene(self, light_id, scene_id):

        relation_list = self.dataDao.getLightSceneRelationList(light_id)

        if len(relation_list) == 0:
            raise Exception("this light not set up scene")

        a_scene = self.dataDao.getScene(scene_id)

        scene_light_status_list = self.dataDao.querySceneLightStatusList(scene_id)

        scene_light_status = None

        if a_scene == None or len(scene_light_status_list) == 0:
            raise Exception("scene_id not fuound")

        for data in scene_light_status_list:
            if data["light_id"] == light_id:
                scene_light_status = data
                break

        light_data = self.dataDao.getLight(light_id, DeviceService.TYPE_SINGLE_LIGHT)

        if scene_light_status == None:
            scene_light_status = scene_light_status_list[0]

        return {"name": a_scene["scene_name"],
                "device-name": self.getNodeByUnicastAddress(light_id).name,
                "lightness": scene_light_status["lightness"],
                "temperature": scene_light_status["temperature"],
                "is_temperature": True if light_data["is_temperature"] == 1 else False,
                "state": True if scene_light_status["on_off"] == 1 else False
                }

    def updateLightScene(self, light_id, scene_id, lightness_per, temperature_per, state):

        relation_list = self.dataDao.getLightSceneRelationList(light_id)

        if len(relation_list) == 0:
            raise Exception("this light not set up scene")

        self.setSingleLightOnOff(light_id, state)
        if state:
            self.setSingleLightLightness(light_id, lightness_per)
            self.setSingleLightTemperature(light_id, temperature_per)

        light_id_ary = self.getLightIdAry(light_id)
        self.callStoreScene(scene_id, light_id_ary)

        scene_light_status = self.dataDao.getSceneLightStatus(scene_id, light_id)
        if scene_light_status == None:
            self.dataDao.saveSceneLightStatus(scene_id, light_id, DeviceService.TYPE_SINGLE_LIGHT,
                                              state, lightness_per, temperature_per)
        else:
            self.dataDao.updateSceneLightStatus(scene_id, light_id, DeviceService.TYPE_SINGLE_LIGHT,
                                                state, lightness_per, temperature_per)

        light_id_ary = self.getLightIdAry(light_id)
        self.callReCallScene(DeviceService.FREEZE_SCENE_ID, light_id_ary)
        self.deleteScene(DeviceService.FREEZE_SCENE_ID)

        return None

    def getLightScheduleList(self, id):
        result_list = []
        alist = self.dataDao.getLightScheduleList(id)
        for adata in alist:
            result_list.append({
                "id": adata["id"],
                "name": adata["schedule_name"]
            })
        return result_list

    def getLightSchedule(self, light_id, id):
        adata = self.dataDao.getLightSchedule(light_id, id)

        sdc = self.getSchedulerClient()

        address_handle = self.getAddressHandle(light_id)
        sdc.publish_set(0, address_handle)
        action = 0

        try:
            data_key_ary = [light_id]
            self.clearRespData(data_key_ary, sdc)

            sdc.schedulerActionGet(adata["schedule_id"])

            result_data = self.getRespData(data_key_ary, self.sdc, 2)
            action = result_data.get(data_key_ary[0])["action"]
        except Exception as e:
            print(e)
            traceback.print_exc()
            print("get schedule action failed")

        return {"name": adata["schedule_name"],
                "id": adata["id"],
                "action": DeviceService.SCEHDULE_LIGHT_ACTION.get(action),
                "week": adata["week"].split(","),
                "hour": adata["hour"],
                "mins": adata["mins"],
                }

    def updateGroupTime(self, group_id):
        print("updateGroupTime group_id:"+str(group_id))
        group_obj = self.getGroupByAddress(group_id)
        print("updateGroupTime group_obj:"+str(group_obj))
        for light_id in group_obj.nodes_unicast_address:
            address_handle = self.getAddressHandle(light_id)
            tsc = self.getTimeClient()
            tsc.publish_set(0, address_handle)
            tsc.timeSet()
        time.sleep(1)

    def updateLightTime(self, light_id):
        print("updateLightTime light_id:"+str(light_id))
        address_handle = self.getAddressHandle(light_id)
        tsc = self.getTimeClient()
        tsc.publish_set(0, address_handle)
        tsc.timeSet()
        time.sleep(1)

    # def getLightUnusedScheduleId(self, light_id):
    #     for i in range(0, 16):
    #         cnt = self.dataDao.countUsedScheduleIdByLightIdList(i, [light_id])
    #         if cnt == 0:
    #             return i
    #     return None

    # def addLightSchedule(self, light_id, schedule_name, schedule_action, week, hour, mins):
    #
    #     schedule_id = self.getLightUnusedScheduleId(light_id)
    #
    #     if schedule_id == None:
    #         raise Exception("light don't found unused schedule-id")
    #
    #     id = self.getSchedulesNewPrimaryKey()
    #     action = DeviceService.SCEHDULE_LIGHT_ACTION.get(schedule_action)
    #
    #     address_handle = self.getAddressHandle(light_id)
    #
    #     tsc = self.getTimeClient()
    #     tsc.publish_set(0, address_handle)
    #     tsc.timeSet()
    #
    #     time.sleep(0.5)
    #
    #     scsc = self.getSchedulerClient()
    #     scsc.publish_set(0, address_handle)
    #
    #     week_byte = [0, 0, 0, 0, 0, 0, 0]
    #
    #     for x in week.split(","):
    #         week_byte[DeviceService.WEEK_MAP[int(x)]] = 1
    #
    #     week_val = int(''.join(str(x) for x in week_byte), 2)
    #
    #     any_month = int('111111111111', 2)
    #
    #     scsc.schedulerActionSet(schedule_id, 0x64, any_month, 0x00, hour, mins, 0, week_val, action, 0, 0)
    #
    #     self.dataDao.saveLightScheduleRelation(light_id, -1, -1, schedule_id)
    #
    #     self.dataDao.saveSchedule(id, schedule_id, DeviceService.TYPE_SINGLE_LIGHT, light_id, -1, schedule_name, action,
    #                               week, hour, mins)

    # def updateLightSchedule(self, id, light_id, schedule_name, schedule_action, week, hour, mins):
    #
    #     schedule_data = self.dataDao.getLightSchedule(light_id, id)
    #
    #     action = DeviceService.SCEHDULE_LIGHT_ACTION.get(schedule_action)
    #
    #     address_handle = self.getAddressHandle(light_id)
    #
    #     tsc = self.getTimeClient()
    #     tsc.publish_set(0, address_handle)
    #     tsc.timeSet()
    #
    #     scsc = self.getSchedulerClient()
    #     scsc.publish_set(0, address_handle)
    #
    #     week_byte = [0, 0, 0, 0, 0, 0, 0]
    #
    #     for x in week.split(","):
    #         week_byte[DeviceService.WEEK_MAP[int(x)]] = 1
    #
    #     week_val = int(''.join(str(x) for x in week_byte), 2)
    #
    #     any_month = int('111111111111', 2)
    #
    #     scsc.schedulerActionSet(schedule_data["schedule_id"], 0x64, any_month, 0x00, hour, mins, 0, week_val, action, 0,
    #                             0)
    #
    #     light_data = self.dataDao.getLight(light_id, DeviceService.TYPE_SINGLE_LIGHT)
    #
    #     if light_data["is_temperature"] == 1:
    #         address_handle = self.getAddressHandle(light_id + 1)
    #         scsc.publish_set(0, address_handle)
    #         scsc.schedulerActionSet(schedule_data["schedule_id"], 0x64, any_month, 0x00, hour, mins, 0, week_val,
    #                                 action, 0, 0)
    #
    #     self.dataDao.updateSchedule(id, schedule_name, action, week, hour, mins)

    # def deleteLightSchedule(self, id, light_id):
    #
    #     schedule_data = self.dataDao.getLightSchedule(light_id, id)
    #
    #     schedule_id = schedule_data["schedule_id"]
    #
    #     address_handle = self.getAddressHandle(light_id)
    #
    #     scsc = self.getSchedulerClient()
    #     scsc.publish_set(0, address_handle)
    #
    #     scsc.schedulerActionSet(schedule_id, 19, 0x00, 0x00, 0, 0, 0, 0, 15, 0, 0)
    #
    #     light_data = self.dataDao.getLight(light_id, DeviceService.TYPE_SINGLE_LIGHT)
    #     if light_data["is_temperature"] == 1:
    #         address_handle = self.getAddressHandle(light_id + 1)
    #         scsc.publish_set(0, address_handle)
    #         scsc.schedulerActionSet(schedule_id, 19, 0x00, 0x00, 0, 0, 0, 0, 15, 0, 0)
    #
    #     # self.dataDao.deleteLightScheduleRelation(schedule_id=schedule_id)
    #     self.dataDao.deleteSchedule(id)

    def getGroupList(self):
        result = []
        for g in self.db.groups:
            group_data = self.dataDao.getLight(g.address.real, DeviceService.TYPE_GROUP)
            nodes = []
            for aNode in self.db.nodes:
                if aNode.unicast_address.real in g.nodes_unicast_address:
                    node = {}
                    device_info = self.getDeviceInfoData(aNode.unicast_address.real)
                    node["id"] = device_info.id
                    node["name"] = aNode.name
                    node["uniAddress"] = aNode.unicast_address.real
                    node["uuid"] = device_info.uuid
                    node["state"] = {
                        "onOff": device_info.switch_state,
                        "level": device_info.dimming_value,
                        "cct": device_info.color_value
                    }
                    nodes.append(node)

            result.append({"id": g.address,
                           "name": g.name,
                           "devices": nodes,
                           "image": group_data["img_path"] if group_data != None else ''})
        return result

    def getGroup(self, id):

        group_obj = self.getGroupByAddress(id)
        group_data = self.dataDao.getLight(id, DeviceService.TYPE_GROUP)

        a_group = {"id": group_obj.address,
                   "name": group_obj.name,
                   "device": [],
                   "image": group_data["img_path"]}

        for aNode in self.db.nodes:
            node = {}
            node["id"] = aNode.unicast_address.real
            node["name"] = aNode.name
            node["inUse"] = True if aNode.unicast_address.real in group_obj.nodes_unicast_address else False
            a_group["device"].append(node)

        return a_group

    def addGroup(self, name, device_list):

        id = self.getNewGroupId()

        is_add_sub_group1 = False

        for light_id in device_list:
            unicast_address = int(light_id)
            light_data = self.getSingleLightData(unicast_address)
            aNode = self.getNodeByUnicastAddress(unicast_address)
            if light_data == None or aNode == None:
                raise Exception('node not exist')

            self.ccPublishSet(unicast_address)
            self.model_add(aNode.unicast_address, id, 0x1000, DeviceService.TYPE_GROUP)
            self.model_add(aNode.unicast_address, id, 0x1002, DeviceService.TYPE_GROUP)
            self.model_add(aNode.unicast_address, id, 0x1204, DeviceService.TYPE_GROUP)
            self.model_add(aNode.unicast_address, id, 0x1203, DeviceService.TYPE_GROUP)
            self.model_add(aNode.unicast_address, id, 0x1206, DeviceService.TYPE_GROUP)
            self.model_add(aNode.unicast_address, id, 0x1207, DeviceService.TYPE_GROUP)

            if light_data.get("is_temperature") == 1:
                self.model_add(aNode.unicast_address + 1, id + 1, 0x1002, DeviceService.TYPE_GROUP)
                self.model_add(aNode.unicast_address + 1, id + 1, 0x1204, DeviceService.TYPE_GROUP)
                self.model_add(aNode.unicast_address + 1, id + 1, 0x1203, DeviceService.TYPE_GROUP)
                self.model_add(aNode.unicast_address + 1, id + 1, 0x1206, DeviceService.TYPE_GROUP)
                self.model_add(aNode.unicast_address + 1, id + 1, 0x1207, DeviceService.TYPE_GROUP)
                is_add_sub_group1 = True

        self.db.groups.append(mt.Group(name, id, nodes_unicast_address=[int(x) for x in device_list]))

        group_info_id = self.getGroupInfoId()
        self.db.groupInfo.append(
            mt.GroupInfo(group_info_id, name, id, id, id, id, id, id + 1, id + 1, id + 1, id + 2, 0, 0))

        for device_addr in device_list:
            group_detail_id = self.getGroupDetailId()
            self.db.groupDetail.append(mt.GroupDetail(group_detail_id, device_addr, group_info_id))

        if is_add_sub_group1:
            self.db.groups[len(self.db.groups) - 1].sub_group1 = id + 1

        self.db.store()

        self.dataDao.saveLight(id, DeviceService.TYPE_GROUP, 1)

        return id

    def addC000Group(self, light_id):

        group_id = DeviceService.ALL_GROUP_ID
        a_node = self.getNodeByUnicastAddress(light_id)

        self.ccPublishSet(light_id)
        self.model_add(a_node.unicast_address, group_id, 0x1000, DeviceService.TYPE_GROUP)
        self.model_add(a_node.unicast_address, group_id, 0x1002, DeviceService.TYPE_GROUP)
        self.model_add(a_node.unicast_address, group_id, 0x1204, DeviceService.TYPE_GROUP)
        self.model_add(a_node.unicast_address, group_id, 0x1203, DeviceService.TYPE_GROUP)
        self.model_add(a_node.unicast_address, group_id, 0x1206, DeviceService.TYPE_GROUP)
        self.model_add(a_node.unicast_address, group_id, 0x1207, DeviceService.TYPE_GROUP)

        self.cc.model_publication_set(a_node.unicast_address, mt.ModelId(0x1000), mt.Publish(group_id, index=0, ttl=5))
        time.sleep(2)
        self.cc.model_publication_set(a_node.unicast_address, mt.ModelId(0x1002), mt.Publish(group_id, index=0, ttl=5))

    def updateGroup(self, id, name, device_list):

        group_obj = self.getGroupByAddress(id)
        group_data = self.getGroupInfoByAddress(id)

        for light_id in device_list:
            unicast_address = int(light_id)

            if unicast_address in group_obj.nodes_unicast_address:
                continue

            light_data = self.getSingleLightData(light_id)
            a_node = self.getNodeByUnicastAddress(unicast_address)
            if a_node == None:
                raise Exception('node not exist')

            self.ccPublishSet(unicast_address)

            self.model_add(a_node.unicast_address, id, 0x1000, DeviceService.TYPE_GROUP)
            self.model_add(a_node.unicast_address, id, 0x1002, DeviceService.TYPE_GROUP)
            self.model_add(a_node.unicast_address, id, 0x1204, DeviceService.TYPE_GROUP)
            self.model_add(a_node.unicast_address, id, 0x1203, DeviceService.TYPE_GROUP)
            self.model_add(a_node.unicast_address, id, 0x1206, DeviceService.TYPE_GROUP)
            self.model_add(a_node.unicast_address, id, 0x1207, DeviceService.TYPE_GROUP)
            if light_data.get("is_temperature") == 1:
                self.model_add(a_node.unicast_address + 1, group_obj.sub_group1, 0x1002, DeviceService.TYPE_GROUP)
                self.model_add(a_node.unicast_address + 1, group_obj.sub_group1, 0x1204, DeviceService.TYPE_GROUP)
                self.model_add(a_node.unicast_address + 1, group_obj.sub_group1, 0x1203, DeviceService.TYPE_GROUP)
                self.model_add(a_node.unicast_address + 1, group_obj.sub_group1, 0x1206, DeviceService.TYPE_GROUP)
                self.model_add(a_node.unicast_address + 1, group_obj.sub_group1, 0x1207, DeviceService.TYPE_GROUP)
            group_detail_id = self.getGroupDetailId()
            self.db.groupDetail.append(mt.GroupDetail(group_detail_id, unicast_address, group_data.id))

        for light_id in group_obj.nodes_unicast_address:
            if str(light_id) in device_list:
                continue
            self.removeLightFormGroup(light_id, id, group_obj)
            del_group_detail = self.getGroupDetailByGroupIdAndDeviceAddress(group_data.id, light_id)
            self.db.groupDetail.remove(del_group_detail)

        group_obj.name = name
        group_obj.nodes_unicast_address = [int(x) for x in device_list]
        self.db.store()

    def updateGroupInfoById(self, id, name, img_file):

        group_obj = self.getGroupByAddress(id)
        group_data = self.dataDao.getLight(id, DeviceService.TYPE_GROUP)

        if img_file is not None:
            if group_data["img_path"] is not None:
                os.remove(DeviceService.IMG_PATH + group_data["img_path"])
            image_name = "G_" + str(datetime.now().timestamp())
            img_file.save(DeviceService.IMG_PATH + image_name)
            self.dataDao.updateLightImage(id, DeviceService.TYPE_GROUP, image_name)

        group_obj.name = name
        self.db.store()

    def deleteGroup(self, id):

        group_obj = self.getGroupByAddress(id)
        group_data = self.dataDao.getLight(id, DeviceService.TYPE_GROUP)

        for light_id in group_obj.nodes_unicast_address:
            self.removeLightFormGroup(light_id, id, group_obj)

        if group_data["img_path"] is not None:
            os.remove(DeviceService.IMG_PATH + group_data["img_path"])

        for i in range(0, len(self.db.groups)):
            if self.db.groups[i].address == id:
                del self.db.groups[i]
                break

        group_info_data = self.getGroupInfoByAddress(id)

        self.db.groupDetail = [x for x in self.db.groupDetail if x.group_ID != group_info_data.id]

        self.db.groupInfo = [x for x in self.db.groupInfo if x.unicast_address != id]

        scene_group_detail_data = self.getSceneGroupDetail(id)
        if scene_group_detail_data is not None:
            scene_num = scene_group_detail_data.scene_num

            self.db.sceneGroupDetail = [x for x in self.db.sceneGroupDetail if x.group_address != id]

            self.db.sceneSingleDetail = [x for x in self.db.sceneSingleDetail if x.group_address != id]

            scene_group_data_count = 0
            for sgdIdx in range(0, len(self.db.sceneGroupDetail)):
                if self.db.sceneGroupDetail[sgdIdx].scene_num == scene_num:
                    scene_group_data_count = scene_group_data_count + 1

            scene_single_data_count = 0
            for ssdIdx in range(0, len(self.db.sceneSingleDetail)):
                if self.db.sceneSingleDetail[ssdIdx].scene_num == scene_num:
                    scene_single_data_count = scene_single_data_count + 1

            if scene_group_data_count == 0 and scene_single_data_count == 0:
                self.db.sceneMain = [x for x in self.db.sceneMain if x.scene_num != scene_num]
                scene_schedule_data = [x for x in self.db.sceneSchedule if x.scene_num == scene_num]
                for ssdIdx in range(0, len(scene_schedule_data)):
                    self.db.sceneScheduleDetail = [x for x in self.db.sceneScheduleDetail if
                                                   x.schedule_id != scene_schedule_data.id]
                self.db.sceneSchedule = [x for x in self.db.sceneSchedule if x.scene_num != scene_num]

        self.db.store()
        self.dataDao.deleteLight(id, DeviceService.TYPE_GROUP)
        self.dataDao.deleteSceneLightStatus(id, light_id=id, light_type=DeviceService.TYPE_GROUP)

    def removeLightFormGroup(self, light_id, group_id, group_obj):

        light_data = self.dataDao.getLight(light_id, DeviceService.TYPE_SINGLE_LIGHT)
        if light_data == None:
            return None

        light_id_ary = self.getLightIdAry(light_id)

        a_node = self.getNodeByUnicastAddress(light_id)
        if a_node == None:
            return None

        self.ccPublishSet(light_id)
        self.light_group_remove(a_node.unicast_address, group_id, 0x1000)
        self.light_group_remove(a_node.unicast_address, group_id, 0x1002)
        self.light_group_remove(a_node.unicast_address, group_id, 0x1204)
        self.light_group_remove(a_node.unicast_address, group_id, 0x1203)
        self.light_group_remove(a_node.unicast_address, group_id, 0x1206)
        self.light_group_remove(a_node.unicast_address, group_id, 0x1207)
        if light_data.get("is_temperature") == 1:
            self.light_group_remove(a_node.unicast_address + 1, group_obj.sub_group1, 0x1002)
            self.light_group_remove(a_node.unicast_address + 1, group_obj.sub_group1, 0x1204)
            self.light_group_remove(a_node.unicast_address + 1, group_obj.sub_group1, 0x1203)
            self.light_group_remove(a_node.unicast_address + 1, group_obj.sub_group1, 0x1206)
            self.light_group_remove(a_node.unicast_address + 1, group_obj.sub_group1, 0x1207)

        light_scene_list = self.dataDao.getLightSceneRelationList(light_id)
        org_light_scene_list = [x["scene_id"] for x in light_scene_list]

        self.dataDao.deleteLightSceneRelation(light_id=light_id, group_id=group_id)

        light_scene_list = self.dataDao.getLightSceneRelationList(light_id)
        new_light_scene_list = [x["scene_id"] for x in light_scene_list]

        for scene_id in org_light_scene_list:
            if scene_id not in new_light_scene_list:
                self.callDeleteScene(scene_id, light_id_ary)

        # self.dataDao.deleteLightScheduleRelation(light_id=light_id, group_id=group_id)

    def setGroupOnOff(self, address_id, onOff, transition_time, repeat, ack):
        """
        """
        group = self.getGroupInfoData(address_id)
        address_handle = self.getAddressHandle(address_id)

        print("setGroupOnOff address_id:"+str(address_id))

        gc = self.getGenericOnOffClient()
        gc.publish_set(0, address_handle)
        gc.set(onOff, ack=bool(ack), transition_time_ms=transition_time, repeat=repeat)
        if onOff == 1:
            group.switch_state = True
        else:
            group.switch_state = False
        if testSaveDb:
            self.updateGroupInfo(group)
        return group

    # gc.set(onOff)
    # gc.set(onOff)

    def setGroupLightness(self, address_id, lightness_per, transition_time, repeat, ack):
        """
            lightness :: -32767~32767
        """
        lightness = 0
        # if lightness_per > 50:
        #     lightness = int((lightness_per - 50) / 50 * 32767)
        #
        #     if lightness > 32767:
        #         lightness = 32767
        # else:
        #     lightness = int((50 - lightness_per) / 50 * -32767)
        #     if lightness < -32767:
        #         lightness = -32767
        group = self.getGroupInfoData(address_id)
        lightness = int((lightness_per / 255) * 65535 - 32768)
        if lightness == -32768:
            lightness = -32767
        address_handle = self.getAddressHandle(address_id)

        glc = self.getGenericLevelClient()
        glc.publish_set(0, address_handle)
        glc.set(lightness, ack=bool(ack), transition_time_ms=transition_time, repeat=repeat)
        group.dimming_value = lightness_per
        if testSaveDb:
            self.updateGroupInfo(group)
        return group

    # glc.set(lightness)
    # glc.set(lightness)

    def setGroupTemperature(self, address_id, temperature_per, transition_time, repeat, ack):
        """
            temperature_per :: 0~ 100s
            temperature :: -32767~32767
        """
        group_obj = self.getGroupByAddress(address_id)

        if group_obj.sub_group1 == None:
            return

        # temperature = 0
        # if temperature_per > 50:
        #     temperature = int((temperature_per - 50) / 50 * 32767)
        #
        #     if temperature > 32767:
        #         temperature = 32767
        # else:
        #     temperature = int((50 - temperature_per) / 50 * -32767)
        #     if temperature < -32767:
        #         temperature = -32767

        group = self.getGroupInfoData(address_id)
        temperature = int((temperature_per / 255) * 65535 - 32768)
        if temperature == -32768:
            temperature = -32767

        address_handle = self.getAddressHandle(group_obj.sub_group1)

        glc = self.getGenericLevelClient()
        glc.publish_set(0, address_handle)
        glc.set(temperature, ack=bool(ack), transition_time_ms=transition_time, repeat=repeat)
        group.color_value = temperature_per
        if testSaveDb:
            self.updateGroupInfo(group)
        return group

    # glc.set(temperature)
    # glc.set(temperature)

    def getNewGroupId(self):
        if len(self.db.groups) > 500:
            raise Exception("group over 500!!")
        if len(self.db.groups) > 0:
            return self.db.groups[len(self.db.groups) - 1].address + 10

        return DeviceService.DEFULT_GROUP_ID

    def getSceneList(self):
        result_list = []

        alist = self.dataDao.querySenceList()

        for data in alist:
            scene_num = data["id"]
            scene_data = self.getSceneMainForSceneNum(scene_num)
            amap = {"id": scene_data.id,
                    "name": data["scene_name"],
                    "sceneNum": data["id"]
                    }
            result_list.append(amap)

        return result_list

    def getNewSceneId(self):

        MAX_NUM = DeviceService.FREEZE_SCENE_ID - 1

        alist = self.getSceneList()

        scene_id_ary = [x["id"] for x in alist]

        if len(scene_id_ary) == 0:
            return 1

        last_id = scene_id_ary[len(scene_id_ary) - 1]

        if last_id < MAX_NUM:
            return last_id + 1

        for i in range(1, MAX_NUM):
            if i not in scene_id_ary:
                return i

        raise Exception("scene id full")

    def addScene(self, name, a_time, a_level, group_list, img_file):

        image_name = None
        if img_file is not None:
            image_name = "SC_" + str(datetime.now().timestamp())
            image_path = DeviceService.IMG_PATH + image_name
            img_file.save(image_path)

        for a_group in group_list:
            if self.checkLightCanAddScene(a_group["id"]) == False:
                raise Exception("device set scene full")

        id = self.getNewSceneId()

        for a_group in group_list:

            group_obj = self.getGroupByAddress(a_group["id"])
            group_id_ary = [a_group["id"], group_obj.sub_group1]

            self.setGroupOnOff(a_group["id"], a_group["state"])
            if a_group["state"]:
                self.setGroupLightness(a_group["id"], a_group["lightness"])
                self.setGroupTemperature(a_group["id"], a_group["temperature"])

            self.callStoreScene(id, group_id_ary)

            self.dataDao.saveSceneLightStatus(id, a_group["id"], DeviceService.TYPE_GROUP,
                                              a_group["state"], a_group["lightness"], a_group["temperature"])

            for light_id in group_obj.nodes_unicast_address:
                self.dataDao.saveLightSceneRelation(light_id, a_group["id"], id)

        self.dataDao.saveScene(id, name, a_time, a_level, image_name)

        a_list = self.dataDao.querySceneLightStatusList(DeviceService.FREEZE_SCENE_ID)
        for a_data in a_list:
            group_id_ary = self.getGroupIdAry(a_data["light_id"])
            self.callReCallScene(DeviceService.FREEZE_SCENE_ID, group_id_ary)
            self.deleteScene(DeviceService.FREEZE_SCENE_ID)

        return id

    def getScene(self, id):
        a_scene = self.dataDao.getScene(id)
        a_list = self.dataDao.querySceneLightStatusList(id)
        a_scene = {"id": a_scene["id"],
                   "name": a_scene["scene_name"],
                   "image": a_scene["img_path"],
                   "time": a_scene["scene_time"],
                   "level": a_scene["scene_level"],
                   "group": []
                   }

        for group_data in a_list:
            a_name = [x.name for x in self.db.groups if x.address.real == group_data["light_id"]]

            a_group = {"id": group_data["light_id"],
                       "name": a_name[0] if len(a_name) > 0 else None,
                       "lightness": group_data["lightness"],
                       "temperature": group_data["temperature"],
                       "state": True if group_data["on_off"] == 1 else False
                       }
            a_scene["group"].append(a_group)
        return a_scene

    def updateScene(self, id, name, a_time, a_level, group_list, img_file):

        scene_data = self.dataDao.getScene(id)

        image_name = scene_data["img_path"]
        if img_file is not None:
            if scene_data["img_path"] is not None:
                os.remove(DeviceService.IMG_PATH + image_name)

            image_name = "SC_" + str(datetime.now().timestamp())
            img_file.save(DeviceService.IMG_PATH + image_name)

        self.dataDao.updateScene(id, name, a_time, a_level, image_name)
        a_list = self.dataDao.querySceneLightStatusList(id)
        scene_group_id_list = [x["light_id"] for x in a_list]
        new_group_list = [x["id"] for x in group_list]

        for x in a_list:
            if x["light_id"] not in new_group_list:

                group_id_ary = self.getGroupIdAry(x["light_id"])
                try:
                    self.callDeleteScene(id, group_id_ary)
                except:
                    pass

                self.dataDao.deleteSceneLightStatus(id, x["light_id"], DeviceService.TYPE_GROUP)

        self.dataDao.deleteLightSceneRelation(scene_id=id)

        for a_group in group_list:

            group_obj = self.getGroupByAddress(a_group["id"])

            group_id_ary = [a_group["id"], group_obj.sub_group1]

            self.setGroupOnOff(a_group["id"], a_group["state"])
            if a_group["state"]:
                self.setGroupLightness(a_group["id"], a_group["lightness"])
                self.setGroupTemperature(a_group["id"], a_group["temperature"])

            self.callStoreScene(id, group_id_ary)

            if a_group["id"] in scene_group_id_list:
                self.dataDao.updateSceneLightStatus(id, a_group["id"], DeviceService.TYPE_GROUP,
                                                    a_group["state"], a_group["lightness"], a_group["temperature"])
            else:
                self.dataDao.saveSceneLightStatus(id, a_group["id"], DeviceService.TYPE_GROUP,
                                                  a_group["state"], a_group["lightness"], a_group["temperature"])

            for light_id in group_obj.nodes_unicast_address:
                self.dataDao.saveLightSceneRelation(light_id, a_group["id"], id)

        a_list = self.dataDao.querySceneLightStatusList(DeviceService.FREEZE_SCENE_ID)
        for a_data in a_list:
            group_id_ary = self.getGroupIdAry(a_data["light_id"])
            self.callReCallScene(DeviceService.FREEZE_SCENE_ID, group_id_ary)
            self.deleteScene(DeviceService.FREEZE_SCENE_ID)

        return None

    def controllScene(self, id, repeat):
        scene_main_data = self.getSceneMainForSceneId(id)
        scene_num = scene_main_data.scene_num
        scene_time = 0
        if scene_num != DeviceService.FREEZE_SCENE_ID:
            a_scene = self.dataDao.getScene(scene_num)
            scene_time = a_scene["scene_time"]

        # a_list = self.dataDao.querySceneLightStatusList(scene_num)
        # if scene_num == DeviceService.FREEZE_SCENE_ID and (a_list == None or len(a_list) == 0):
        #     a_list = self.dataDao.querySceneLightStatusList(scene_num, DeviceService.TYPE_SINGLE_LIGHT)
        #     if a_list is not None and len(a_list) > 0:
        #         light_id_ary = self.getLightIdAry(a_list[0]["light_id"])
        #         self.callReCallScene(scene_num, light_id_ary, scene_time, 0, a_list[0]["on_off"] == 1)
        # else:
        #     for a_group in a_list:
        #         group_id_ary = self.getGroupIdAry(a_group["light_id"])
        #         self.callReCallScene(scene_num, group_id_ary, scene_time, 0, a_group["on_off"] == 1)

        a_list = self.dataDao.querySceneLightStatusList(scene_num, DeviceService.TYPE_SINGLE_LIGHT)
        if a_list is not None and len(a_list) > 0:
            for a_device in a_list:
                light_id_ary = self.getLightIdAry(a_device["light_id"])
                self.callReCallScene(scene_num, light_id_ary, scene_time, 0, a_device["on_off"] == 1, repeat)

        a_list = self.dataDao.querySceneLightStatusList(scene_num, DeviceService.TYPE_GROUP)
        if a_list is not None and len(a_list) > 0:
            for a_group in a_list:
                group_id_ary = self.getGroupIdAry(a_group["light_id"])
                self.callReCallScene(scene_num, group_id_ary, scene_time, 0, a_group["on_off"] == 1, repeat)

        return None

    def deleteScene(self, id):

        scene_data = self.dataDao.getScene(id)

        schedule_id_list = self.dataDao.queryUseSceneScheduleIdList(id)

        if schedule_id_list != None and len(schedule_id_list) > 0:
            raise Exception("schedule use this scene")
        if scene_data is not None and scene_data["img_path"] is not None:
            os.remove(DeviceService.IMG_PATH + scene_data["img_path"])

        a_list = self.dataDao.querySceneLightStatusList(id, None)
        for a_data in a_list:
            try:
                id_ary = None
                if a_data["light_type"] == DeviceService.TYPE_GROUP:
                    id_ary = self.getGroupIdAry(a_data["light_id"])
                else:
                    id_ary = self.getLightIdAry(a_data["light_id"])

                self.callDeleteScene(id, id_ary)
            except:
                pass

        schedule_list = self.dataDao.getSceneScheduleList()

        for data in schedule_list:
            if data["scene_id"] == id:
                self.deleteSchedule(data["id"])

        self.dataDao.deleteLightSceneRelation(scene_id=id)
        self.dataDao.deleteSceneLightStatus(id)
        self.dataDao.deleteScene(id)

        return None

    def checkLightCanAddScene(self, group_id):
        group_obj = self.getGroupByAddress(group_id)

        for light_id in group_obj.nodes_unicast_address:
            r_list = self.dataDao.getLightSceneRelationList(light_id)
            if len(r_list) >= 15:
                return False

        return True

    def initFreezeScene(self, scene_id, light_id):

        self.deleteScene(DeviceService.FREEZE_SCENE_ID)

        if scene_id != -1:
            if light_id == -1:
                a_list = self.dataDao.querySceneLightStatusList(scene_id)
                for a_data in a_list:
                    group_id_ary = self.getGroupIdAry(a_data["light_id"])
                    self.callStoreScene(DeviceService.FREEZE_SCENE_ID, group_id_ary)
                    self.dataDao.saveSceneLightStatus(DeviceService.FREEZE_SCENE_ID, a_data["light_id"],
                                                      DeviceService.TYPE_GROUP, 0, 0, 0)
            else:
                light_id_ary = self.getLightIdAry(light_id)
                self.callStoreScene(DeviceService.FREEZE_SCENE_ID, light_id_ary)
                self.dataDao.saveSceneLightStatus(DeviceService.FREEZE_SCENE_ID, light_id,
                                                  DeviceService.TYPE_SINGLE_LIGHT, 0, 0, 0)

    def updateGroupForFreezeScene(self, unuse_group_id, use_group_id):

        if unuse_group_id != -1:
            group_id_ary = self.getGroupIdAry(unuse_group_id)
            self.callReCallScene(DeviceService.FREEZE_SCENE_ID, group_id_ary)
            self.callDeleteScene(DeviceService.FREEZE_SCENE_ID, group_id_ary)
            self.dataDao.deleteSceneLightStatus(DeviceService.FREEZE_SCENE_ID, unuse_group_id, DeviceService.TYPE_GROUP)

        if use_group_id != -1:
            group_id_ary = self.getGroupIdAry(use_group_id)
            self.callStoreScene(DeviceService.FREEZE_SCENE_ID, group_id_ary)
            self.dataDao.saveSceneLightStatus(DeviceService.FREEZE_SCENE_ID, use_group_id, DeviceService.TYPE_GROUP, 0,
                                              0, 0)

    def getScheduleList(self):
        result_list = []
        alist = self.dataDao.getSceneScheduleList()
        for adata in alist:
            schedule_id = adata["id"]
            schedule_data = self.getSceneScheduleForId(schedule_id)
            result_list.append({
                "id": adata["id"],
                "name": adata["schedule_name"],
                "sceneNum": adata["scene_id"],
                "startTime": None if schedule_data is None else schedule_data.start_time,
                "repeatWeekly": None if schedule_data is None else schedule_data.repeat_weekly
            })
        return result_list

    def getSceneSchedule(self, id):
        alist = self.dataDao.getSceneScheduleList()
        for adata in alist:
            if adata["id"] == id:
                schedule_id = adata["id"]
                schedule_data = self.getSceneScheduleForId(schedule_id)
                return {
                    "id": adata["id"],
                    "name": adata["schedule_name"],
                    "sceneNum": adata["scene_id"],
                    "startTime": None if schedule_data is None else schedule_data.start_time,
                    "repeatWeekly": None if schedule_data is None else schedule_data.repeat_weekly
                }

        return None
        # adata = self.dataDao.getSceneSchedule(id)
        # if adata is None:
        #     return None
        # schedule_id = adata["id"]
        # schedule_data = self.getSceneScheduleForId(schedule_id)
        #
        # return {
        #     "id": adata["id"],
        #     "name": adata["schedule_name"],
        #     "sceneNum": adata["scene_id"],
        #     "startTime": None if schedule_data is None else schedule_data.start_time,
        #     "repeatWeekly": None if schedule_data is None else schedule_data.repeat_weekly
        # }

    def addScheduleNew(self, schedule_name, scene_id, weeks, hours, mins,onlyCheckScheduleNum):

        # schedule_id = self.getCommonUnusedScheduleIdBySceneId(scene_id)
        # if schedule_id == None:
        #     raise Exception("scene's lights don't found common unused schedule-id")

        id = self.getSchedulesNewPrimaryKey()

        week_byte = [0, 0, 0, 0, 0, 0, 0]

        for x in weeks.split(","):
            week_byte[DeviceService.WEEK_MAP[int(x)]] = 1

        week_val = int(''.join(str(x) for x in week_byte), 2)

        print("week_val:" + str(week_val))
        str_hours = "%02d" % hours
        print("str_hours:" + str(str_hours))
        str_mins = "%02d" % mins
        print("str_mins:" + str(str_mins))
        str_week = bin(week_val)[2:]
        str_week = str_week.zfill(7)
        print("str_week:" + str(str_week))
        str_start_time = str_hours + ":" + str_mins

        #做出已使用的schedule_id_map
        schedule_id_map = {}
        for dataSceneScheduleDetail in self.db.sceneScheduleDetail:
            if dataSceneScheduleDetail.single_address in schedule_id_map:
                schedule_id_map[dataSceneScheduleDetail.single_address][dataSceneScheduleDetail.schedule_num] = 1
            else:
                schedule_id_map[dataSceneScheduleDetail.single_address] = {}
                schedule_id_map[dataSceneScheduleDetail.single_address][dataSceneScheduleDetail.schedule_num] = 1
        # print("self.db.sceneScheduleDetail:"+str(self.db.sceneScheduleDetail))
        # 測試數據
        # schedule_id_map[8][4] = 1
        # schedule_id_map[8][5] = 1
        print("schedule_id_map:"+str(schedule_id_map))

        #準備組合群組
        scene_group_list3 = self.dataDao.querySceneLightStatusList(scene_id=scene_id,light_type=3)
        scene_group_list1 = self.dataDao.querySceneLightStatusList(scene_id=scene_id,light_type=1)
        my_groups = []
        for group_data in scene_group_list3:
            group_obj = self.getGroupByAddress(group_data["light_id"])
            my_groups.append(group_obj.nodes_unicast_address)
        for group_data in scene_group_list1:
            my_groups.append([group_data["light_id"]])

        # 測試數據
        # my_groups = [[4, 8, 12, 16], [4] ,[1,2],[2,3],[5,6],[1,5]]
        # my_groups = [[4 ,12], [4],[8],[16] ,[8,16]]
        print("my_groups:"+str(my_groups))

        my_combine_groups = self.combineGroup(my_groups)
        print("my_combine_groups:"+str(my_combine_groups))



        tmp_min_schedule_id = {}
        for my_combine_group in my_combine_groups:
            get_null_schedule_id = True
            for i in range(16):
                print("i:" + str(i))
                hit = 0
                for light_id in my_combine_group:
                    if light_id in schedule_id_map and i in schedule_id_map[light_id]:
                        hit = 1
                        print("light_id hit:"+str(light_id)+",i:"+str(i))
                        break
                if hit == 0:
                    for light_id in my_combine_group:
                        tmp_min_schedule_id[light_id] = i
                    print("tmp_schedule_id = " + str(i))
                    get_null_schedule_id = False
                    break
            if get_null_schedule_id:
                return 0

        #只做檢查的,現在回應1就可了,不用往下作(檢查不合格的,上面就return了)
        if onlyCheckScheduleNum:
            return 1

        print("tmp_min_schedule_id:"+str(tmp_min_schedule_id))

        for group_data in scene_group_list3:
            group_id = group_data["light_id"]
            group_obj = self.getGroupByAddress(group_id)
            light_id = group_obj.nodes_unicast_address[0]
            schedule_id = tmp_min_schedule_id[light_id]
            print("set:"+str(group_id)+","+str(light_id)+","+str(schedule_id))
            self.updateGroupTime(group_id)
            address_handle = self.getAddressHandle(group_id)
            scsc = self.getSchedulerClient()
            scsc.publish_set(0, address_handle)
            any_month = int('111111111111', 2)
            scsc.schedulerActionSet(schedule_id, 0x64, any_month, 0x00, hours, mins, 0, week_val, 2, 0, scene_id)
        for group_data in scene_group_list1:
            light_id = group_data["light_id"]
            schedule_id = tmp_min_schedule_id[light_id]
            print("set:"+str(light_id)+","+str(tmp_min_schedule_id[light_id]))
            self.updateLightTime(light_id)
            address_handle = self.getAddressHandle(light_id)
            scsc = self.getSchedulerClient()
            scsc.publish_set(0, address_handle)
            any_month = int('111111111111', 2)
            scsc.schedulerActionSet(schedule_id, 0x64, any_month, 0x00, hours, mins, 0, week_val, 2, 0, scene_id)

        print("id:" + str(id))
        print("scene_id:" + str(scene_id))
        for light_id in tmp_min_schedule_id:
            scene_schedule_detail_id = self.getSceneScheduleDetailId()
            schedule_id = tmp_min_schedule_id[light_id]
            print("scene_schedule_detail_id:"+str(scene_schedule_detail_id))
            print("light_id:"+str(light_id))
            print("schedule_id:"+str(schedule_id))
            self.db.sceneScheduleDetail.append(mt.SceneScheduleDetail(id=scene_schedule_detail_id,schedule_id=id,scene_num=scene_id,single_address=light_id,schedule_num=schedule_id,action=2,group_address=0))

        self.dataDao.saveSchedule(id, schedule_id, DeviceService.TYPE_SCENE, -1, scene_id, schedule_name, 2, weeks,hours, mins)
        self.db.sceneSchedule.append(mt.SceneSchedule(id, scene_id, schedule_name, str_start_time, str_week, 2))
        self.db.store()
        return id

    # 測試數據
    # my_groups = [[4, 8, 12, 16], [4] ,[1,2],[2,3],[5,6],[1,5]]
    # my_groups = [[4 ,12], [4],[8],[16] ,[8,16]]
    def combineGroup(self, groups):
        if len(groups) > 1:
            for groupA in groups:
                for groupB in groups:
                    if groupA == groupB:
                        print("同組不處理")
                    else:
                        if len(list(set(groupA).intersection(set(groupB)))) > 0:
                            new_groups = []
                            new_groups.append(list(set(groupA).union(set(groupB))))
                            for groupC in groups:
                                if groupC != groupA and groupC != groupB:
                                    new_groups.append(groupC)
                            return self.combineGroup(new_groups)
        return groups

    # def addSchedule(self, schedule_name, scene_id, weeks, hours, mins):
    #
    #     schedule_id = self.getCommonUnusedScheduleIdBySceneId(scene_id)
    #     if schedule_id == None:
    #         raise Exception("scene's lights don't found common unused schedule-id")
    #
    #     id = self.getSchedulesNewPrimaryKey()
    #
    #     week_byte = [0, 0, 0, 0, 0, 0, 0]
    #
    #     for x in weeks.split(","):
    #         week_byte[DeviceService.WEEK_MAP[int(x)]] = 1
    #
    #     week_val = int(''.join(str(x) for x in week_byte), 2)
    #
    #     print("week_val:" + str(week_val))
    #     str_hours = "%02d" % hours
    #     print("str_hours:" + str(str_hours))
    #     str_mins = "%02d" % mins
    #     print("str_mins:" + str(str_mins))
    #     str_week = bin(week_val)[2:]
    #     str_week = str_week.zfill(7)
    #     print("str_week:" + str(str_week))
    #     str_start_time = str_hours + ":" + str_mins
    #
    #     scene_group_list = self.dataDao.querySceneLightStatusList(scene_id=scene_id,light_type=None)
    #
    #     for group_data in scene_group_list:
    #
    #         group_obj = self.getGroupByAddress(group_data["light_id"])
    #         if group_obj is not None:
    #             self.updateGroupTime(group_data["light_id"])
    #
    #         address_handle = self.getAddressHandle(group_data["light_id"])
    #         scsc = self.getSchedulerClient()
    #         scsc.publish_set(0, address_handle)
    #
    #         any_month = int('111111111111', 2)
    #         scsc.schedulerActionSet(schedule_id, 0x64, any_month, 0x00, hours, mins, 0, week_val, 2, 0, scene_id)
    #
    #         if group_obj is not None and group_obj.sub_group1 is not None:
    #             address_handle = self.getAddressHandle(group_obj.sub_group1)
    #             scsc.publish_set(0, address_handle)
    #             scsc.schedulerActionSet(schedule_id, 0x64, any_month, 0x00, hours, mins, 0, week_val, 2, 0, scene_id)
    #
    #     lihgt_scene_list = self.dataDao.getLightSceneRelationLisBySceneId(scene_id)
    #
    #     for data in lihgt_scene_list:
    #         self.dataDao.saveLightScheduleRelation(data["light_id"], data["group_id"], scene_id, schedule_id)
    #         scene_schedule_detail_id = self.getSceneScheduleDetailId()
    #         self.db.sceneScheduleDetail.append(
    #             mt.SceneScheduleDetail(scene_schedule_detail_id, id, scene_id, data["light_id"], schedule_id, 2,
    #                                    data["group_id"]))
    #
    #     self.dataDao.saveSchedule(id, schedule_id, DeviceService.TYPE_SCENE, -1, scene_id, schedule_name, 2, weeks,
    #                               hours, mins)
    #     self.db.sceneSchedule.append(mt.SceneSchedule(id, scene_id, schedule_name, str_start_time, str_week, 2))
    #     self.db.store()
    #     return id

    # def getCommonUnusedScheduleIdBySceneId(self, scene_id):
    #     light_id_list = []
    #     group_list = self.dataDao.querySceneLightStatusList( scene_id=scene_id,light_type=None)
    #
    #     for a_group in group_list:
    #         group_obj = self.getGroupByAddress(a_group["light_id"])
    #         if group_obj is not None:
    #             for light_id in group_obj.nodes_unicast_address:
    #                 if light_id not in light_id_list:
    #                     light_id_list.append(light_id)
    #         else:
    #             light_id_list.append(a_group["light_id"])
    #
    #     for i in range(0, 16):
    #         cnt = self.dataDao.countUsedScheduleIdByLightIdList(i, light_id_list)
    #         if cnt == 0:
    #             return i
    #     return None

    def getSchedulesNewPrimaryKey(self):
        schedule_data = self.dataDao.queryMaxScheduleId()

        if schedule_data == None:
            return 0
        else:
            return schedule_data["id"] + 1

    # def queryLightScheduleUseStatus(self):
    #     result_map = {}
    #
    #     all_list = self.dataDao.queryAllLightUsedScheduleList()
    #
    #     for data in all_list:
    #         id = data["light_id"]
    #         alist = result_map.get(id) if result_map.get(id) is not None else [0] * 16
    #         alist.insert(data["schedule_id"], data["schedule_id"])
    #         result_map[id] = alist

    # def updateSchedule(self, id, schedule_name, weeks, hours, mins):
    #     week_byte = [0, 0, 0, 0, 0, 0, 0]
    #     for x in weeks.split(","):
    #         week_byte[DeviceService.WEEK_MAP[int(x)]] = 1
    #
    #     week_val = int(''.join(str(x) for x in week_byte), 2)
    #
    #     schedule = self.dataDao.getSceneSchedule(id)
    #
    #     print("updateSchedule schedule:"+str(schedule))
    #
    #     scene_id = schedule["scene_id"]
    #
    #     schedule_id = schedule["schedule_id"]
    #
    #     print("week_val:" + str(week_val))
    #     str_hours = "%02d" % hours
    #     print("str_hours:" + str(str_hours))
    #     str_mins = "%02d" % mins
    #     print("str_mins:" + str(str_mins))
    #     str_week = bin(week_val)[2:]
    #     str_week = str_week.zfill(7)
    #     print("str_week:" + str(str_week))
    #     str_start_time = str_hours + ":" + str_mins
    #
    #     scene_group_list = self.dataDao.querySceneLightStatusList(scene_id=schedule["scene_id"], light_type = None)
    #     print("updateSchedule scene_group_list:"+str(scene_group_list))
    #
    #     for group_data in scene_group_list:
    #
    #         group_obj = self.getGroupByAddress(group_data["light_id"])
    #         # print("updateSchedule group_obj:" + str(group_obj))
    #         print("updateSchedule group_data[light_id]:" + str(group_data["light_id"]))
    #         if group_obj is not None :
    #             print("updateSchedule group_data[light_id]:" + str(group_data["light_id"]))
    #             self.updateGroupTime(group_data["light_id"])
    #         print("updateSchedule group_obj end")
    #
    #         address_handle = self.getAddressHandle(group_data["light_id"])
    #
    #         scsc = self.getSchedulerClient()
    #         scsc.publish_set(0, address_handle)
    #
    #         any_month = int('111111111111', 2)
    #
    #         scsc.schedulerActionSet(schedule_id, 0x64, any_month, 0x00, hours, mins, 0, week_val, 2, 0, scene_id)
    #
    #         if group_obj is not None and group_obj.sub_group1 is not None:
    #             address_handle = self.getAddressHandle(group_obj.sub_group1)
    #             scsc.publish_set(0, address_handle)
    #             scsc.schedulerActionSet(schedule_id, 0x64, any_month, 0x00, hours, mins, 0, week_val, 2, 0, scene_id)
    #
    #     # self.dataDao.deleteLightScheduleRelation(schedule_id=schedule_id)
    #     #
    #     # self.db.sceneScheduleDetail = [x for x in self.db.sceneScheduleDetail if x.schedule_id != id]
    #     #
    #     # lihgt_scene_list = self.dataDao.getLightSceneRelationLisBySceneId(scene_id)
    #     # print("updateSchedule lihgt_scene_list:"+str(lihgt_scene_list))
    #     #
    #     # for data in lihgt_scene_list:
    #     #     self.dataDao.saveLightScheduleRelation(data["light_id"], data["group_id"], scene_id, schedule_id)
    #     #     scene_schedule_detail_id = self.getSceneScheduleDetailId()
    #     #     self.db.sceneScheduleDetail.append(
    #     #         mt.SceneScheduleDetail(scene_schedule_detail_id, id, scene_id, data["light_id"], schedule_id, 2,
    #     #                                data["group_id"]))
    #     #
    #     self.dataDao.updateSchedule(id, schedule_name, 2, weeks, hours, mins)
    #     for ssIdx in range(0, len(self.db.sceneSchedule)):
    #         if self.db.sceneSchedule[ssIdx].id == id:
    #             self.db.sceneSchedule[ssIdx].schedule_name = schedule_name
    #             self.db.sceneSchedule[ssIdx].start_time = str_start_time
    #             self.db.sceneSchedule[ssIdx].repeat_weekly = str_week
    #             self.db.sceneSchedule[ssIdx].action = 2
    #             break
    #     self.db.store()


    def updateScheduleNew(self, id,sceneNum, schedule_name, weeks, hours, mins):
        week_byte = [0, 0, 0, 0, 0, 0, 0]
        for x in weeks.split(","):
            week_byte[DeviceService.WEEK_MAP[int(x)]] = 1

        week_val = int(''.join(str(x) for x in week_byte), 2)
        print("week_val:" + str(week_val))
        str_hours = "%02d" % hours
        print("str_hours:" + str(str_hours))
        str_mins = "%02d" % mins
        print("str_mins:" + str(str_mins))
        str_week = bin(week_val)[2:]
        str_week = str_week.zfill(7)
        print("str_week:" + str(str_week))
        str_start_time = str_hours + ":" + str_mins

        schedule = self.dataDao.getScheduleById(id)

        print("updateSchedule schedule new:"+str(schedule))

        old_scene_id = schedule["scene_id"]

        if sceneNum == old_scene_id:
            if gl.get_value("MORE_LOG"):
                print("sceneNum沒改變")

            # print("self.db.sceneScheduleDetail:"+str(self.db.sceneScheduleDetail))
            # print("self.db.sceneSingleDetail:"+str(self.db.sceneSingleDetail))
            doScheduleMap = {}
            for dataSceneScheduleDetail in self.db.sceneScheduleDetail:
                if dataSceneScheduleDetail.schedule_id == id:
                    get_group_address = 0
                    for dataSceneSingleDetail in self.db.sceneSingleDetail:
                        if dataSceneSingleDetail.single_address == dataSceneScheduleDetail.single_address and dataSceneSingleDetail.scene_num == dataSceneScheduleDetail.scene_num :
                            if dataSceneSingleDetail.group_address > 0:
                                get_group_address = dataSceneSingleDetail.group_address
                                schedule_id = dataSceneScheduleDetail.schedule_num
                                if dataSceneSingleDetail.group_address in doScheduleMap and doScheduleMap[dataSceneSingleDetail.group_address] == schedule_id :
                                    #同群組只需做一次,同schedule_id
                                    print("already do:"+str(dataSceneSingleDetail.group_address))
                                else:
                                    self.updateGroupTime(dataSceneSingleDetail.group_address)
                                    address_handle = self.getAddressHandle(dataSceneSingleDetail.group_address)
                                    scsc = self.getSchedulerClient()
                                    scsc.publish_set(0, address_handle)
                                    any_month = int('111111111111', 2)
                                    scsc.schedulerActionSet(schedule_id, 0x64, any_month, 0x00, hours, mins, 0, week_val, 2,
                                                            0, old_scene_id)
                                    doScheduleMap[dataSceneSingleDetail.group_address] = schedule_id
                                break

                    if get_group_address == 0:
                        self.updateLightTime(dataSceneScheduleDetail.single_address)
                        address_handle = self.getAddressHandle(dataSceneScheduleDetail.single_address)
                        schedule_id = dataSceneScheduleDetail.schedule_num
                        scsc = self.getSchedulerClient()
                        scsc.publish_set(0, address_handle)
                        any_month = int('111111111111', 2)
                        scsc.schedulerActionSet(schedule_id, 0x64, any_month, 0x00, hours, mins, 0, week_val, 2,
                                                0, old_scene_id)

            self.dataDao.updateSchedule(id, schedule_name, 2, weeks, hours, mins)
            for ssIdx in range(0, len(self.db.sceneSchedule)):
                if self.db.sceneSchedule[ssIdx].id == id:
                    self.db.sceneSchedule[ssIdx].schedule_name = schedule_name
                    self.db.sceneSchedule[ssIdx].start_time = str_start_time
                    self.db.sceneSchedule[ssIdx].repeat_weekly = str_week
                    self.db.sceneSchedule[ssIdx].action = 2
                    break
            self.db.store()
            return 1
        else:
            if gl.get_value("MORE_LOG"):
                print("sceneNum已改變")
            #先做檢查
            ok = self.addScheduleNew(schedule_name, sceneNum, weeks, hours, mins ,1)
            if ok == 0:
                return ok
            self.deleteScheduleNew(id)
            ok = self.addScheduleNew(schedule_name, sceneNum, weeks, hours, mins ,0)
            return ok

    def deleteScheduleNew(self, id):

        doScheduleMap = {}
        for dataSceneScheduleDetail in self.db.sceneScheduleDetail:
            if dataSceneScheduleDetail.schedule_id == id:
                get_group_address = 0
                for dataSceneSingleDetail in self.db.sceneSingleDetail:
                    if dataSceneSingleDetail.single_address == dataSceneScheduleDetail.single_address and dataSceneSingleDetail.scene_num == dataSceneScheduleDetail.scene_num:
                        if dataSceneSingleDetail.group_address > 0:
                            get_group_address = dataSceneSingleDetail.group_address
                            if dataSceneSingleDetail.group_address in doScheduleMap:
                                # 同群組只需做一次
                                print("already do:" + str(dataSceneSingleDetail.group_address))
                            else:
                                address_handle = self.getAddressHandle(dataSceneSingleDetail.group_address)
                                schedule_id = dataSceneScheduleDetail.schedule_num
                                scsc = self.getSchedulerClient()
                                scsc.publish_set(0, address_handle)
                                scsc.schedulerActionSet(schedule_id, 19, 0x00, 0x00, 0, 0, 0, 0, 15, 0, 0)
                                doScheduleMap[dataSceneSingleDetail.group_address] = 1

                if get_group_address == 0:
                    address_handle = self.getAddressHandle(dataSceneScheduleDetail.single_address)
                    schedule_id = dataSceneScheduleDetail.schedule_num
                    scsc = self.getSchedulerClient()
                    scsc.publish_set(0, address_handle)
                    scsc.schedulerActionSet(schedule_id, 19, 0x00, 0x00, 0, 0, 0, 0, 15, 0, 0)

        self.dataDao.deleteSchedule(id)
        self.db.sceneScheduleDetail = [x for x in self.db.sceneScheduleDetail if x.schedule_id != id]
        self.db.sceneSchedule = [x for x in self.db.sceneSchedule if x.id != id]
        self.db.store()


    # def deleteSchedule(self, id):
    #
    #     schedule_data = self.dataDao.getSceneSchedule(id)
    #
    #     schedule_id = schedule_data["schedule_id"]
    #
    #     scene_id = schedule_data["scene_id"]
    #
    #     scene_group_list = self.dataDao.querySceneLightStatusList(scene_id)
    #
    #     for group_data in scene_group_list:
    #
    #         group_obj = self.getGroupByAddress(group_data["light_id"])
    #
    #         address_handle = self.getAddressHandle(group_data["light_id"])
    #
    #         scsc = self.getSchedulerClient()
    #         scsc.publish_set(0, address_handle)
    #         scsc.schedulerActionSet(schedule_id, 19, 0x00, 0x00, 0, 0, 0, 0, 15, 0, 0)
    #
    #         if group_obj.sub_group1 is not None:
    #             address_handle = self.getAddressHandle(group_obj.sub_group1)
    #             scsc.publish_set(0, address_handle)
    #             scsc.schedulerActionSet(schedule_id, 19, 0x00, 0x00, 0, 0, 0, 0, 15, 0, 0)
    #
    #     self.dataDao.deleteLightScheduleRelation(schedule_id=schedule_id)
    #     self.dataDao.deleteSchedule(id)
    #     self.db.sceneScheduleDetail = [x for x in self.db.sceneScheduleDetail if x.schedule_id != id]
    #     self.db.sceneSchedule = [x for x in self.db.sceneSchedule if x.id != id]
    #     self.db.store()

    # def getSceneLightSetScheduleCountList(self, scene_id):
    #     result_list = []
    #     light_list = []
    #     group_list = self.dataDao.querySceneLightStatusList(scene_id)
    #
    #     for a_group in group_list:
    #         group_obj = self.getGroupByAddress(a_group["light_id"])
    #
    #         for light_id in group_obj.nodes_unicast_address:
    #             if light_id in light_list:
    #                 continue
    #             light_obj = self.getNodeByUnicastAddress(light_id)
    #             rel_list = self.dataDao.getLightScheduleRelationList(light_id)
    #             result_list.append({"device": light_obj.name,
    #                                 "id": light_id,
    #                                 "count": len(rel_list)})
    #             light_list.append(light_id)
    #     return result_list

    def startSensor(self, sensor_data, group_id_ary, cadence):

        self.stopSensor()

        sc = self.getSensorClient()

        for group_id in group_id_ary:
            handle_address = self.getAddressHandle(group_id)
            sc.publish_set(0, handle_address)
            sc.publish_set(0, handle_address)

            sc.settingSet(240, 0x13, sensor_data["major_range"] + sensor_data["minor_range"], ack=False)
            time.sleep(1)
            sc.settingSet(240, 0x11, sensor_data["v1"], ack=False)
            time.sleep(1)
            sc.settingSet(240, 0x12, sensor_data["uuid"], ack=False)
            time.sleep(2)

            self.device.send(cmd.AddrSubscriptionAdd(group_id))
            time.sleep(1)

            sc.cadenceSet(240, cadence, ack=False)

        self.sensor_group_ary = group_id_ary
        self.run_sensor = sensor_data["id"]

    def stopSensor(self):
        if self.run_sensor != -1 and self.sensor_group_ary is not None:
            for group_id in self.sensor_group_ary:
                handle_address = self.getAddressHandle(group_id)
                sc = self.getSensorClient()
                sc.publish_set(0, handle_address)
                sc.cadenceSet(240, 0, ack=False, repeat=3)
                time.sleep(0.5)
                self.device.send(cmd.AddrSubscriptionRemove(group_id))
                time.sleep(0.5)

        self.sensor_group_ary = None
        self.run_sensor = -1

    def getSensorStreamData(self):
        data_map = self.device.last_cmd_resp_dict.get(evt.Event.MESH_MESSAGE_RECEIVED_SUBSCRIPTION)
        result_list = []
        for key, data in data_map.items():
            if data is not None and data.get("get_time") is not None \
                    and datetime.timestamp(datetime.now()) - datetime.timestamp(data["get_time"]) < 3:
                result = {
                    # "src" : data["src"],
                    # "rssi" : data["rssi"],
                    # "data" : data["data"],
                    # 'adv_addr_type' : data["adv_addr_type"],
                    # 'actual_length' : data["actual_length"],
                    # 'adv_addr' : data["adv_addr"],
                    # 'ttl' : data["ttl"],
                    # 'dst' : data["dst"],
                    # 'appkey_handle' : data["appkey_handle"],
                    # 'subnet_handle' : data["subnet_handle"],
                    'data_src': data["src"],
                    # 'data_ttl' : data["data_ttl"],
                    'data_majorID': data["data_majorID"],
                    'data_minorID': data["data_minorID"],
                    'data_rssi': data["data_rssi"],
                    # 'data_timestamp' : data["data_timestamp"],
                    'data_ImprovedDistance': data["data_ImprovedDistance"]
                }

                data["get_time"] = None
                result_list.append(result)
        return result_list

    def getSensorStreamObject(self):
        data_map = self.device.last_cmd_resp_dict.get(evt.Event.MESH_MESSAGE_RECEIVED_SUBSCRIPTION)
        result_map = {}
        for key, data in data_map.items():
            if data is not None and data.get("get_time") is not None \
                    and datetime.timestamp(datetime.now()) - datetime.timestamp(data["get_time"]) < 10:
                result = {
                    "src": data["src"],
                    "rssi": data["rssi"],
                    "data": data["data"],
                    'adv_addr_type': data["adv_addr_type"],
                    'actual_length': data["actual_length"],
                    'adv_addr': data["adv_addr"],
                    'ttl': data["ttl"],
                    'dst': data["dst"],
                    'appkey_handle': data["appkey_handle"],
                    'subnet_handle': data["subnet_handle"],
                    'data_ttl': data["data_ttl"],
                    'data_majorID': data["data_majorID"],
                    'data_minorID': data["data_minorID"],
                    'data_rssi': data["data_rssi"],
                    'data_ImprovedDistance': data["data_ImprovedDistance"],
                    'data_timestamp': data["data_timestamp"],
                    'get_time': data["get_time"]
                }

                data["get_time"] = None
                result_map[key] = result

        return result_map

    def callReCallScene(self, scene_id, device_id_ary, transition_time=0, delay=0, is_open=True, repeat=1):
        sc = self.getSceneClient()
        if is_open and device_id_ary[1] is not None:
            address_handle = self.getAddressHandle(device_id_ary[1])
            sc.publish_set(0, address_handle)
        sc.sceneRecall(scene_id, transition_time_ms=transition_time, delay_ms=delay, ack=False, repeat=1)
        time.sleep(0.2)

    def callStoreScene(self, scene_id, device_id_ary):
        ssc = self.getSceneClient()
        address_handle = self.getAddressHandle(device_id_ary[0])
        ssc.publish_set(0, address_handle)
        ssc.sceneStore(scene_id, ack=False)

        time.sleep(3)
        if device_id_ary[1] is not None:
            address_handle = self.getAddressHandle(device_id_ary[1])
            ssc.publish_set(0, address_handle)
            ssc.sceneStore(scene_id, ack=False)
            time.sleep(3)

    def callDeleteScene(self, scene_id, device_id_ary):
        ssc = self.getSceneClient()
        address_handle = self.getAddressHandle(device_id_ary[0])
        ssc.publish_set(0, address_handle)
        ssc.sceneDelete(scene_id)
        time.sleep(0.2)
        if device_id_ary[1] is not None:
            address_handle = self.getAddressHandle(device_id_ary[1])
            ssc.publish_set(0, address_handle)
            ssc.sceneDelete(scene_id)
            time.sleep(0.2)

    def updateTime(self):
        for aNode in self.db.nodes:
            address_handle = self.getAddressHandle(aNode.unicast_address.real)
            tsc = self.getTimeClient()
            tsc.publish_set(0, address_handle)
            tsc.timeSet()
            time.sleep(0.5)

    def startDeviceMonitor(self):
        self.run_monitor = 1
        self.device.send(cmd.AddrSubscriptionAdd(DeviceService.ALL_GROUP_ID))

    def stopDeviceMonitor(self):
        self.run_monitor = -1
        data_key_ary = [RespOpcode.ADDR_SUBSCRIPTION_ADD_RSP]
        self.clearRespData(data_key_ary, self.provisioning)
        self.device.send(cmd.AddrSubscriptionAdd(DeviceService.ALL_GROUP_ID))

        result_data = self.getRespData(data_key_ary, self.provisioning, 5)
        handle_id = result_data.get(data_key_ary[0])[0]

        self.device.send(cmd.AddrSubscriptionRemove(handle_id))

    def getDeviceMonitorStreamData(self):
        data_map1 = self.device.last_cmd_resp_dict.get("ON_OFF")
        data_map2 = self.device.last_cmd_resp_dict.get("lightness")

        result_list = []
        for key, data in data_map1.items():
            if data is not None and data.get("get_time") is not None \
                    and datetime.timestamp(datetime.now()) - datetime.timestamp(data["get_time"]) < 5:
                result = {
                    "src": data["src"],
                    "rssi": data["rssi"],
                    "data": data["data"],
                    'adv_addr_type': data["adv_addr_type"],
                    'actual_length': data["actual_length"],
                    'adv_addr': data["adv_addr"],
                    'ttl': data["ttl"],
                    'dst': data["dst"],
                    'appkey_handle': data["appkey_handle"],
                    'subnet_handle': data["subnet_handle"],
                    'on_off': data["on_off"]
                }

                data["get_time"] = None
                result_list.append(result)

        for key, data in data_map2.items():
            if data is not None and data.get("get_time") is not None \
                    and datetime.timestamp(datetime.now()) - datetime.timestamp(data["get_time"]) < 5:
                result = {
                    "src": data["src"],
                    "rssi": data["rssi"],
                    "data": data["data"],
                    'adv_addr_type': data["adv_addr_type"],
                    'actual_length': data["actual_length"],
                    'adv_addr': data["adv_addr"],
                    'ttl': data["ttl"],
                    'dst': data["dst"],
                    'appkey_handle': data["appkey_handle"],
                    'subnet_handle': data["subnet_handle"],
                    'lightness': data["lightness"]
                }

                data["get_time"] = None
                result_list.append(result)

        return result_list

    def getDeviceMonitorStreamList(self):
        while self.run_monitor != -1:
            time.sleep(0.1)
            result_list = self.getDeviceMonitorStreamData()
            if len(result_list) > 0:
                yield 'data: {}\n\n'.format(json.dumps({"list": result_list}))
        return 'end'

    def setLsbuEnergyTime(self, id, propertyID, hours, transition_time, repeat):
        flagOfstatus = True

        address_handle = self.getAddressHandle(id)
        device = self.getDeviceInfoData(id)
        if device is not None:
            lc = self.getLsbuClient()

            retry = 5
            timeout = 3
            retrySleep = 0.1
            for i in range(0, retry):
                try:
                    lc.publish_set(0, address_handle)

                    ''' Get device composition data(product id, version id, fw version) and store in dictionary named
                        "devicePublishInfoDict". '''
                    if str(id) not in lc.devicePublishInfoDict:
                        data_key_ary = [str(id) + "compositionData"]
                        self.clearRespData(data_key_ary, lc)

                        feedback = 5
                        lc.requestCompositionData(feedback)

                        result_data = self.getRespData(data_key_ary, lc, timeout - 1)
                        if result_data != {}:
                            print("get Lsbu composition data ok:")
                        else:
                            time.sleep(retrySleep)
                    time.sleep(0.2)
                    ''' Get the power ratio.
                        Get the max mA and calculate the max Power walt. '''
                    if str(id) not in lc.deviceMaxPowerRatioDict:
                        data_key_ary = [str(id) + "PowerRatio"]
                        self.clearRespData(data_key_ary, lc)

                        lc.settingGet(0x0006)

                        result_data = self.getRespData(data_key_ary, lc, timeout)
                        if result_data != {}:
                            print("get Lsbu PowerRatio data ok:")
                        else:
                            time.sleep(retrySleep)

                    time.sleep(0.2)
                    ''' Get the energy log from device which is raw data. '''
                    data_key_ary = [str(id) + "Energy"]
                    self.clearRespData(data_key_ary, lc)

                    lc.set(propertyID, hours, transition_time_ms=transition_time, repeat=repeat)

                    result_data = self.getRespData(data_key_ary, lc, timeout)

                    if result_data != {}:
                        print("getLsbuEnergy ok:")
                        flagOfstatus = False
                        # self.callback_energy_log(id, hours, lc.last_cmd_resp_dict[data_key_ary[0]], lc.devicePublishInfoDict, lc.deviceMaxPowerRatioDict)
                        break
                    else:
                        time.sleep(retrySleep)
                except:
                    pass

        return {'id': id,
                'name': device.name,
                'uniAddress': device.unicast_address,
                'deviceDescription': device.device_description,
                'transitionTime': transition_time,
                'repeat': repeat,
                'timeout': True if flagOfstatus is True else False,
                'state': {
                    'productId': lc.devicePublishInfoDict[str(id)]['productId'],
                    'ratio': lc.deviceMaxPowerRatioDict[str(id)],
                    'data': lc.last_cmd_resp_dict[data_key_ary[0]]
                    }
                }



    def enterdfu(self, id):
        flagOfstatus = True

        address_handle = self.getAddressHandle(id)
        device = self.getDeviceInfoData(id)
        if device is not None:

            lc = self.getLsbuClient()

            lc.publish_set(0, address_handle)
            lc.enterDfuMode(id)


class RespOpcode(object):
    PROVISION_RESP_DEV_HANDLE_CODE = 156
    PROVISION_RESP_ADDRESS_HANDLE_CODE = 164
    RESP_ADDR_GET_ALL = 168
    RESP_ADDR_GET = 167
    ADDR_SUBSCRIPTION_ADD_RSP = 0xA1
