import sys
import logging
import DateTime
import os
import json
from datetime import datetime
import time
# import threading

this_file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,this_file_dir+'/..')
import globalvar as gl

import threading

from aci.aci_utils import STATUS_CODE_LUT
from aci.aci_config import ApplicationConfig
from aci import aci_cmd as cmd
from aci import aci_evt as evt
from mesh import access
from mesh.database import MeshDB  # NOQA: ignore unused import


#是否有訂閱Group(須改成與deviceService.py的設定一致)
SUB_STATUS = gl.get_value('SUB_STATUS')

#收到RX,是否更新回裝置的狀態(True:會更新,False:不會更新)
updateDeviceStatus = gl.get_value('updateDeviceStatus')

displayMeshMsg = True

FILE_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s: %(message)s"
STREAM_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s: %(message)s"

LOG_DIR = os.path.join(os.path.split(os.path.realpath(__file__))[0], "log")

def getDeviceConfig(filePath, name):
    """INTERNAL FUNCTION"""
    with open(filePath, "r") as confFh:
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

class Interactive(object):
    DEFAULT_APP_KEY = bytearray([0x4c, 0x53, 0x42, 0x55, 0x45, 0x61, 0x73, 0x79, 0x43, 0x6f, 0x6e, 0x66, 0x69, 0x67, 0x53, 0x57])
    DEFAULT_SUBNET_KEY = bytearray([0x4c, 0x53, 0x42, 0x55, 0x45, 0x61, 0x73, 0x79, 0x43, 0x6f, 0x6e, 0x66, 0x97, 0x57, 0xcc, 0xae])
    DEFAULT_VIRTUAL_ADDRESS = bytearray([0xCC] * 16)
    DEFAULT_STATIC_AUTH_DATA = bytearray([0xDD] * 16)
    localUnicastAddr = 0x7fff

    aPath = os.path.split(os.path.realpath(__file__))[0]

    ##os.path.join(os.path.split(os.path.realpath(__file__))[0],
    ##                             ("data/"
    ##                              + "nrf_mesh_config_app.h")))
    ##if os.path.isfile("data/LTDMS.json"):
    # if os.path.isfile(os.path.join(aPath, "data/LTDMS.json")):
    #     with open(os.path.join(aPath, "data/LTDMS.json"), "r+", encoding='utf-8-sig') as confFh:
            # content = confFh.read()
    #         content = confFh.read()
    #         if len(content) > 0:
    #             conf = json.loads(content)
    #             if "MeshInfo" in conf and "provisionedData" in conf["MeshInfo"] and\
    #             "provisioners" in conf["MeshInfo"]["provisionedData"] and\
    #             len(conf["MeshInfo"]["provisionedData"]["provisioners"][0]) > 0 and\
    #             "provisionerAddress" in conf["MeshInfo"]["provisionedData"]["provisioners"][0]:
    #                 localUnicastAddr = int(conf["MeshInfo"]["provisionedData"]["provisioners"][0]["provisionerAddress"], 16)
                # save to config file
    #             updateConfig("unicastAddress", localUnicastAddr)
    ##elif os.path.isfile("data/config.json"):
    if os.path.isfile(os.path.join(aPath, "data/config.json")):
        uni = getDeviceConfig(os.path.join(aPath, "data/config.json"), "unicastAddress")
        if uni is not False:
            localUnicastAddr = uni
        # conf = json.loads(open("data/config.json", "rb").read())
        # if "deviceInfo" in conf and "unicastAddress" in conf["deviceInfo"]:
        #     localUnicastAddr = conf["deviceInfo"]["unicastAddress"]

    DEFAULT_LOCAL_UNICAST_ADDRESS_START = localUnicastAddr
    print("interactive.py DEFAULT_LOCAL_UNICAST_ADDRESS_START:"+str(DEFAULT_LOCAL_UNICAST_ADDRESS_START))
    CONFIG = ApplicationConfig(
        header_path=os.path.join(os.path.split(os.path.realpath(__file__))[0],
                                 ("include/"
                                  + "nrf_mesh_config_app.h")))
    PRINT_ALL_EVENTS = True

    def __init__(self, acidev,myDEFAULT_LOCAL_UNICAST_ADDRESS_START=DEFAULT_LOCAL_UNICAST_ADDRESS_START):
        self.acidev = acidev
        self._event_filter = []
        self._event_filter_enabled = False
        #True
        self._other_events = []

        self.logger = configure_logger(self.acidev.device_name)
        self.send = self.acidev.write_aci_cmd

        self.DEFAULT_LOCAL_UNICAST_ADDRESS_START = myDEFAULT_LOCAL_UNICAST_ADDRESS_START
        # Increment the local unicast address range
        # for the next Interactive instance
        self.local_unicast_address_start = (self.DEFAULT_LOCAL_UNICAST_ADDRESS_START)
        # Interactive.DEFAULT_LOCAL_UNICAST_ADDRESS_START += (
        # Interactive.DEFAULT_LOCAL_UNICAST_ADDRESS_START -= (
        #     self.CONFIG.ACCESS_ELEMENT_COUNT)

        self.access = access.Access(self, self.local_unicast_address_start,
                                    self.CONFIG.ACCESS_ELEMENT_COUNT)
        self.model_add = self.access.model_add

        # Adding the packet recipient will start dynamic behavior.
        # We add it after all the member variables has been defined
        self.acidev.add_packet_recipient(self.__event_handler)
        self.last_cmd_resp_dict = {}
        self.last_cmd_resp_dict["ON_OFF"] = {}
        self.last_cmd_resp_dict["lightness"] = {}
        self.last_cmd_resp_dict[evt.Event.MESH_MESSAGE_RECEIVED_SUBSCRIPTION] = {}

        self.callback_C000 = None
        self.callback_C001 = None

        self.my_sub_group_list = list()
        self.my_sub_group_address_handle_list = list()
        self.my_sub_group_address_handle_list_map = {}
        self.my_sub_group_list_type_map = {}
        self.callback_group_onoff = None
        self.callback_switch_onoff = None
        self.callback_group_lightness = None
        self.callback_group_temperature = None
        self.callback_house_open_door = None
        self.callback_iBeacon_sensor_info = None


        self.house_open_door = {}
        self.house_open_door_time = {}

        # onoff time interval thread
        if gl.get_value("server_device_check_lost_onoff"):
            self.set_interval(self.check_lost_device, gl.get_value("server_device_check_lost_every_sec") )

        # onoff device cadence time interval thread
        if gl.get_value("server_device_cadence_time_interval_onoff"):
            self.set_interval(self.update_device_cadence, gl.get_value("server_device_cadence_interval"))

    def set_my_sub_group_list(self, my_sub_group_list_new):
        self.my_sub_group_list = my_sub_group_list_new.copy()

    def set_my_sub_group_list_type(self, my_key,my_value):
        self.my_sub_group_list_type_map[my_key] = my_value

    def set_my_sub_group_address_handle_list(self, my_sub_group_address_handle_list_new):
        self.my_sub_group_address_handle_list = my_sub_group_address_handle_list_new.copy()
        for i in range(len(self.my_sub_group_address_handle_list)):
            self.my_sub_group_address_handle_list_map[ self.my_sub_group_address_handle_list[i] ] = self.my_sub_group_list[i]

    def setC0000(self, callback):
        self.callback_C000 = callback

    def setC0001(self, callback):
        self.callback_C001 = callback

    def set_callback_group_onoff(self, callback):
        self.callback_group_onoff = callback

    def set_callback_switch_onoff(self, callback):
        self.set_callback_switch_onoff = callback

    def set_callback_group_lightness(self, callback):
        self.callback_group_lightness = callback

    def set_callback_switch_lightness(self, callback):
        self.set_callback_switch_lightness = callback

    def set_callback_group_temperature(self, callback):
        self.callback_group_temperature = callback

    def set_callback_switch_temperature(self, callback):
        self.set_callback_switch_temperature = callback

    def set_callback_house_open_door(self, callback):
        self.callback_house_open_door = callback

    def set_callback_iBeacon_sensor_info(self, callback):
        self.callback_iBeacon_sensor_info = callback




    def close(self):
        self.acidev.stop()

    def events_get(self):
        return self._other_events

    def event_filter_add(self, event_filter):
        self._event_filter += event_filter

    def event_filter_disable(self):
        self._event_filter_enabled = False

    def event_filter_enable(self):
        self._event_filter_enabled = True

    def device_port_get(self):
        return self.acidev.serial.port

    def quick_setup(self):
        self.send(cmd.SubnetAdd(0, bytearray(self.DEFAULT_SUBNET_KEY)))
        self.send(cmd.AppkeyAdd(0, 0, bytearray(self.DEFAULT_APP_KEY)))
        self.send(cmd.AddrLocalUnicastSet(
            self.local_unicast_address_start,
            self.CONFIG.ACCESS_ELEMENT_COUNT))


    # def reload_setup(self):
    #     db_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], ("database/example_database.json"))
    #     db = MeshDB(path=db_path)
    #     #        db = MeshDB(path="database/example_database.json")
    #     self.DEFAULT_SUBNET_KEY = db.net_keys[0].key
    #     self.DEFAULT_APP_KEY = db.app_keys[0].key
    #     self.send(cmd.SubnetAdd(0, bytearray(self.DEFAULT_SUBNET_KEY)))
    #     self.send(cmd.AppkeyAdd(0, 0, bytearray(self.DEFAULT_APP_KEY)))
    #     self.send(cmd.AddrLocalUnicastSet(
    #         self.local_unicast_address_start,
    #         self.CONFIG.ACCESS_ELEMENT_COUNT))

    '''
    1.在mesh裡面的裝置才可以有權限進來從uart傳送資料，因為dongle C裡面必須要配置才會有動作；反之，在ＦＷ裡面的rx_cb就是全部
      ibeacon都接收，所以基本上只要有設定可以發送ibeacon就會進到這個rx_cb.
    2.event.
    '''
    def __event_handler(self, event):
        # t = threading.currentThread()
        # print('Thread id : %d' % t.ident)

        global displayMeshMsg
        if gl.get_value('MORE_LOG'):
            print("=============== start ===============")

            print("event._event_name:" + str(event._event_name))
            print("event._opcode:" + str(event._opcode))
            print("event._data:" + str(event._data))
            if "data" in event._data:
                data = ['%02x' % b for b in event._data["data"]]
                print("data:" + str(data) )
            print("=============== end ===============")

        if self._event_filter_enabled and event._opcode in self._event_filter:
            # Ignore event
            return
        if event._opcode == evt.Event.DEVICE_STARTED:
            isRebootFlag = True
            self.logger.info("Device rebooted.")

        elif "opcode" in event._data.keys() and event._data["opcode"] == 0xAC:
            self.logger.info("Device State Cleared.")

        elif event._opcode == evt.Event.CMD_RSP:
            if event._data["status"] != 0:
                self.logger.error("{}: {}".format(
                    cmd.response_deserialize(event),
                    STATUS_CODE_LUT[event._data["status"]]["code"]))
            else:
                text = str(cmd.response_deserialize(event))
                if text == "None":
                    text = "Success"
                self.logger.info(text)
        else:

            if self.PRINT_ALL_EVENTS and event is not None and gl.get_value('PROCESS_READY'):
                # 处理client subscription数据
                #if isinstance(event, evt.MeshMessageReceivedSubscription):
                if event._opcode is evt.Event.MESH_MESSAGE_RECEIVED_SUBSCRIPTION:
                    unicast_address = event._data['src']
                    ttl = event._data['ttl']
                    act_length = event._data["actual_length"]
                    data = ['%02x' % b for b in event._data["data"]]
                    msg = ""
                    
                    result_map = {
                        'src':unicast_address,
                        'rssi':event._data['rssi'],
                        'data':"".join(data),
                        'adv_addr_type':event._data["adv_addr_type"],
                        'actual_length':act_length,
                        'adv_addr':['%02x' % b for b in event._data["adv_addr"]],
                        'ttl':ttl,
                        'dst':event._data['dst'],
                        'appkey_handle':event._data['appkey_handle'],
                        'subnet_handle':event._data['subnet_handle'],
                        'get_time':datetime.now(),
                        'data_hex':data,
                        'dst_group_address_id':self.my_sub_group_list[event._data['dst']]
                        }

                    # print("=============== start ===============")
                    # print("event._data:"+str(result_map))
                    # print("=============== end ===============")


                    if act_length == 11 and int(data[4], 16) == 1:
                        majorID = int(data[5], 16) << 8 | int(data[6], 16)
                        minorID = int(data[7], 16) << 8 | int(data[8], 16)
                        signalPower = int(data[9], 16)
                        rssi = int(data[10], 16) - 256
                        msg = "iBeacon, unicastAddress:" + str(unicast_address) \
                            + ",ttl:" + str(ttl) \
                            + ",majorID:" + str(majorID) \
                            + ",minorID:" + str(minorID) + ",signalPower:" \
                            + str(signalPower) + ",Rssi:" + str(rssi)
                    elif act_length == 12 and int(data[4], 16) == 3:
                        macAddress = data[11] + ":" + data[10] + ":" + data[9] \
                        + ":" + data[8] + ":" + data[7] + ":" + data[6]
                        batteryLevel = int(data[12], 16)
                        msg = "DeviceInfo, unicastAddress:" + str(unicast_address) \
                            + ",ttl:" + str(ttl) \
                            + ",macAddress:" + macAddress \
                            + ",batteryLevel:" + str(batteryLevel)
                    elif act_length == 16 and int(data[4], 16) == 2:
                        macAddress = str(data[6]) + ":" + str(data[7]) + ":" \
                        + str(data[8]) + ":" + str(data[9]) + ":" + str(data[10]) \
                        + ":" + str(data[11])
                        voltage = '%.2f' % ((int(data[12], 16) << 8 | int(data[13], 16)) * 0.001)
                        temp = int(data[14], 16) + (int(data[15], 16) / 255.0)
                        msg = "EddyStone, unicastAddress:" + str(unicast_address) \
                            + ",ttl:" + str(ttl) \
                            + ",macAddress:" + macAddress \
                            + ",voltage:" + str(voltage) + ", temp:" + str(temp)
                    elif act_length == 21 and int(data[4], 16) == 4:
                        nc = int(data[4], 16)
                        sos = int(data[5], 16)
                        step = int(data[6], 16) << 16 | int(data[7], 16) << 8 | int(data[8], 16)
                        heartBeat = int(data[9], 16)
                        sleep = '%04X' % (int(data[10], 16) << 8 | int(data[11], 16))
                        battery = int(data[12], 16)
                        currentHour = int(data[13], 16)
                        currentMinute = int(data[14], 16)
                        bloodPHigh = int(data[15], 16)
                        bloodPLow = int(data[16], 16)
                        oxygen = int(data[17], 16)
                        deviceAddress = '%04X' % (int(data[18], 16) << 8 | int(data[19], 16))
                        msg = "unicastAddress:" + str(unicast_address) \
                            + ", ttl:" + str(ttl) \
                            + ", SmartWatchBeacon, nc:" + ('佩戴' if nc == 1 else '离手') \
                            + ", sos:" + ('SOS' if sos == 1 else '保险') + ", walkingStep:" + str(step) \
                            + ", heartBeat:" + str(heartBeat) + "BPM, sleep:" + sleep \
                            + ", battery:" + str(battery) + ", currentTime:" + str(currentHour) + ":" + str(currentMinute) \
                            + ", bloodPHigh:" + str(bloodPHigh) + "mmHg, bloodPLow:" + str(bloodPLow) \
                            + "mmHg, oxygen:" + str(oxygen) + "%, deviceAddress:" + deviceAddress
                    elif act_length == 11 and int(data[4], 16) == 5:
                        majorID = int(data[5], 16) << 8 | int(data[6], 16)
                        minorID = int(data[7], 16) << 8 | int(data[8], 16)
                        dist = int(data[9], 16)
                        rssi = int(data[10], 16) - 256
                        distance = "immediate" if dist == 0 else ("near" if dist == 1 else ("far" if dist == 2 else "unknown")) 
                        msg = "iBeaconDistance, unicastAddress:" + str(unicast_address) \
                            + ",ttl:" + str(ttl) \
                            + ",majorID:" + str(majorID) \
                            + ",minorID:" + str(minorID) + ",Rssi:" + str(rssi) \
                            + ",Distance:" + distance
                    elif act_length == 11 and int(data[4], 16) == 6:
                        majorID = int(data[5], 16) << 8 | int(data[6], 16)
                        minorID = int(data[7], 16) << 8 | int(data[8], 16)
                        dist = int(data[9], 16)
                        rssi = int(data[10], 16) - 256
                        distance = "immediate" if dist == 0 else ("near" if dist == 1 else ("far" if dist == 2 else "unknown")) 
                        msg = "ImprovediBeaconDistance:" + distance + ",unicastAddress:" + str(unicast_address) \
                            + ",ttl:" + str(ttl) \
                            + ",majorID:" + str(majorID) \
                            + ",minorID:" + str(minorID) + ",Rssi:" + str(rssi) \

                        result_map["data_ttl"] = str(ttl)
                        result_map["data_majorID"] = str(majorID)
                        result_map["data_minorID"] = str(minorID)
                        result_map["data_rssi"] = rssi
                        result_map["data_ImprovedDistance"] = distance
                        result_map["data_timestamp"] = datetime.now().timestamp() * 1000
                        self.last_cmd_resp_dict[evt.Event.MESH_MESSAGE_RECEIVED_SUBSCRIPTION][str(majorID) + "|" + str(minorID) + "|" + str(unicast_address)] = result_map

                        if self.callback_iBeacon_sensor_info is not None:
                            self.callback_iBeacon_sensor_info(result_map)

                    elif act_length ==3 and int(data[0], 16) == 130 and int(data[1],16) == 4:

                        result_map["on_off"] = int(data[2], 16)
                        self.last_cmd_resp_dict["ON_OFF"][str(unicast_address)] = result_map

                        if gl.get_value('MORE_LOG'):
                            print("my ON_OFF:"+str(result_map))

                        if self.callback_C000 is not None and updateDeviceStatus:
                            self.callback_C000(result_map["on_off"],unicast_address)

                    elif act_length ==4 and int(data[0], 16) == 130 and int(data[1],16) == 8:
                        present_level = int(data[3], 16) << 8 | int(data[2], 16)
                        if present_level > 32767:
                            present_level -= 65536
                        
                        result_map["lightness"] = present_level
                        self.last_cmd_resp_dict["lightness"][str(unicast_address)] = result_map

                        if gl.get_value('MORE_LOG'):
                            print("my lightness:"+str(result_map))

                        if self.callback_C001 is not None and updateDeviceStatus:
                            self.callback_C001(result_map["lightness"],unicast_address)


                    #安房 date:52 40 08 0x  //and int(data[1],16) == 64 and int(data[2],16) == 8 中間兩碼不用檢查
                    elif act_length == 4 and int(data[0], 16) == 82:
                        open_door = int(data[3], 16)
                        self.house_open_door_time[str(unicast_address)] = time.time()
                        if str(unicast_address) in self.house_open_door:
                            if self.house_open_door[str(unicast_address)] != open_door:
                                self.house_open_door[str(unicast_address)] = open_door
                                result_map["open_door"] = open_door
                                if gl.get_value('MORE_LOG'):
                                    print("open_door result_map:" + str(result_map))
                                    print("unicast_address:" + str(unicast_address))
                                    print("open_door:" + str(open_door))
                                if self.callback_house_open_door is not None:
                                    self.callback_house_open_door(open_door, unicast_address)
                        # First been searched will enter else.
                        else:
                            self.house_open_door[str(unicast_address)] = open_door
                            result_map["open_door"] = open_door
                            if gl.get_value('MORE_LOG'):
                                print("First open_door result_map:" + str(result_map))
                                print("unicast_address:" + str(unicast_address))
                                print("First open_door:" + str(open_door))
                            if self.callback_house_open_door is not None:
                                self.callback_house_open_door(open_door, unicast_address)

                    #test for pir(4 bytes) and lux(6 bytes) -- can delete if needed
                    elif act_length == 6 and int(data[0], 16) == 82:
                        luxValue = int(data[3], 16)
                        luxValue1 = int(data[4], 16)
                        luxValue2 = int(data[5], 16)
                        self.house_open_door_time[unicast_address] = time.time()
                        if gl.get_value('MORE_LOG'):
                            print("lux: " + str(luxValue))
                            print("lux1: " + str(luxValue1))
                            print("lux2: " + str(luxValue2))

                    # Group onOff server callback.(From switch control)
                    # Opcode (hex)data[0] = 82, data[1] = 03
                    elif act_length == 6 and (int(data[0], 16) == 130 and int(data[1], 16) == 3):
                        result_map["on_off"] = int(data[2], 16)
                        self.last_cmd_resp_dict["ON_OFF"][str(unicast_address)] = result_map
                        dst_group_address_id = self.my_sub_group_list[event._data['dst']]

                        if gl.get_value('MORE_LOG'):
                            print("my ON_OFF:" + str(result_map))
                            print("group onOff address:" + str(dst_group_address_id))

                        if self.set_callback_switch_onoff is not None:
                            self.set_callback_switch_onoff(result_map["on_off"], data, result_map["src"], dst_group_address_id)
                        else:
                            if gl.get_value('MORE_LOG'):
                                print("set_callback_switch_onoff is None")

                    # Collected EddyStone TLM Beacon
                    #elif act_length == 11 and (int(data[0], 16) == 2 and int(data[1], 16) == 32):
                    #    if gl.get_value('MORE_LOG'):



                    else:
                        if event._data['src'] >= 32267 and event._data['src'] <= 32767 and SUB_STATUS:
                            if int(data[0], 16) == 130 and int(data[1],16) == 3:
                                result_map["on_off"] = int(data[2], 16)
                                #address_id = self.my_sub_group_address_handle_list_map[event._data['dst']]
                                dst_group_address_id = self.my_sub_group_list[event._data['dst']]

                                if gl.get_value('MORE_LOG'):
                                    print( "my ON_OFF: address_id:"+ str(dst_group_address_id)  )
                                    print( "my ON_OFF: my_sub_group_list_type_map:"+ self.my_sub_group_list_type_map[ dst_group_address_id ]  )

                                if self.callback_group_onoff is not None and updateDeviceStatus:
                                    self.callback_group_onoff(result_map["on_off"], dst_group_address_id)
                                else:
                                    if gl.get_value('MORE_LOG'):
                                        print("callback_group_onoff is None")

                            elif int(data[0], 16) == 130 and int(data[1],16) == 7:
                                present_level = int(data[3], 16) << 8 | int(data[2], 16)
                                if present_level > 32767:
                                    present_level -= 65536
                                result_map["lightness"] = present_level
                                address_id = self.my_sub_group_address_handle_list_map[event._data['dst']]

                                if gl.get_value('MORE_LOG'):
                                    print( "my lightness: address_id:"+ str( address_id ))
                                    print( "my lightness: my_sub_group_list_type_map:"+ self.my_sub_group_list_type_map[ address_id ]  )

                                if self.my_sub_group_list_type_map[ address_id ] is not None:
                                    if self.my_sub_group_list_type_map[ address_id ] == "base0":
                                        if self.callback_group_lightness is not None and updateDeviceStatus:
                                            self.callback_group_lightness(result_map["lightness"], address_id)
                                        else:
                                            if gl.get_value('MORE_LOG'):
                                                print("callback_group_lightness is None")
                                    elif self.my_sub_group_list_type_map[ address_id ] == "base1":
                                        if self.callback_group_temperature is not None and updateDeviceStatus:
                                            self.callback_group_temperature(result_map["lightness"], address_id-1)
                                        else:
                                            if gl.get_value('MORE_LOG'):
                                                print("callback_group_temperature is None")

                        # print("other log :" + str(result_map))
                        if gl.get_value('MORE_LOG'):
                            self.logger.info(str(event))
                    if msg != '':
                        if displayMeshMsg:
                            if gl.get_value('MORE_LOG'):
                                self.logger.info(msg)

            else:
                self._other_events.append(event)


    def set_interval(self,func, sec):
        def func_wrapper():
            self.set_interval(func, sec)
            func()
        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t

    def check_lost_device(self):
        time_2 = time.time()
        for key in self.house_open_door:
            if gl.get_value('MORE_LOG'):
                print(key, '->', self.house_open_door[key])
            if self.house_open_door[key] == 1:
                time_interval = time_2 - self.house_open_door_time[key]
                if gl.get_value('MORE_LOG'):
                    print(key, ' time_interval: ', time_interval)
                if time_interval > gl.get_value("server_device_lost_sec"):
                    self.house_open_door[key] = 0
                    if gl.get_value('MORE_LOG'):
                        print("check_lost_device lost:", key)
                    if self.callback_house_open_door is not None:
                        self.callback_house_open_door(0, key)


    def update_device_cadence(self):
        time_2 = time.time()
        for key in self.house_open_door:
            if gl.get_value('MORE_LOG'):
                print('Cadence: ', key, '->', self.house_open_door[key])
            time_interval = time_2 - self.house_open_door_time[key]
            if gl.get_value('MORE_LOG'):
                print('Cadence: ', key, ' time_interval: ', time_interval)
            if time_interval < gl.get_value("server_device_lost_sec"):
                if gl.get_value('MORE_LOG'):
                    print("update_device_cadence: ", key)
                if self.callback_house_open_door is not None:
                    self.callback_house_open_door(self.house_open_door[key], key)


def configure_logger(device_name):
    '''global options '''
    no_logfile = True

    logger = logging.getLogger(device_name)
    logger.setLevel(logging.DEBUG)

    need_pop = 1
    if not logger.handlers:
        need_pop = 0

    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)
    if need_pop == 1:
        if gl.get_value('MORE_LOG'):
            print("configure_logger device_name0:" + device_name + " need_pop:" + str(need_pop) + " handlers:" + str(len(logger.handlers)))
        logger.handlers.pop()

    if not no_logfile:
        dt = DateTime.DateTime()
        logfile = "{}_{}-{}-{}-{}_output.log".format(
            device_name, dt.yy(), dt.dayOfYear(), dt.hour(), dt.minute())
        logfile = os.path.join(LOG_DIR, logfile)
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(FILE_LOG_FORMAT)
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)
        if need_pop == 1:
            if gl.get_value('MORE_LOG'):
                print("configure_logger device_name0:" + device_name + " need_pop:" + str(need_pop) + " handlers:" + str(len(logger.handlers)))
            logger.handlers.pop()


    return logger
