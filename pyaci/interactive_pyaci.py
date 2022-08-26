# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2020, Nordic Semiconductor ASA
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of Nordic Semiconductor ASA nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL NORDIC SEMICONDUCTOR ASA OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import sys
# Command below is to Disable pyc file generate.
sys.dont_write_bytecode = True
if sys.version_info < (3, 5):
    print(("ERROR: To use {} you need at least Python 3.5.\n" +
           "You are currently using Python {}.{}").format(sys.argv[0], *sys.version_info))
    sys.exit(1)

import logging
import IPython
import DateTime
import os
import colorama
from subprocess import check_output

from argparse import ArgumentParser
import traitlets.config

this_file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,this_file_dir+'/..')
import globalvar as gl

#要在其他py起來前執行讀取參數的動作
gl.read_config_ini()
gl.read_env()

from aci.aci_uart import Uart
from aci.aci_utils import STATUS_CODE_LUT
from aci.aci_config import ApplicationConfig
import aci.aci_cmd as cmd
import aci.aci_evt as evt

from mesh import access
from mesh.provisioning import Provisioner, Provisionee  # NOQA: ignore unused import
from mesh import types as mt  # NOQA: ignore unused import
from mesh.database import MeshDB  # NOQA: ignore unused import
from models.config import ConfigurationClient  # NOQA: ignore unused import
from models.generic_on_off import GenericOnOffClient  # NOQA: ignore unused import
from models.generic_on_off_flash import GenericOnOffFlashClient  # NOQA: ignore unused import
from models.generic_level import GenericLevelClient
from models.sensor import SensorClient  # NOQA: ignore unused import

from models.time import TimeClient
from models.scene import SceneClient
from models.scheduler import SchedulerClient

from models.lsbu import LsbuClient

import threading
from threading import Timer
import time
import hashlib

import json
import struct
import re
from shutil import copy2

LOG_DIR = os.path.join(os.path.dirname(sys.argv[0]), "log")

USAGE_STRING = \
    """
    {c_default}{c_text}To control your device, use {c_highlight}d[x]{c_text}, where x is the device index.
    Devices are indexed based on the order of the COM ports specified by the -d option.
    The first device, {c_highlight}d[0]{c_text}, can also be accessed using {c_highlight}device{c_text}.

    Type {c_highlight}d[x].{c_text} and hit tab to see the available methods.
"""  # NOQA: Ignore long line
USAGE_STRING += colorama.Style.RESET_ALL

FILE_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s: %(message)s"
STREAM_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s: %(message)s"
COLOR_LIST = [colorama.Fore.MAGENTA, colorama.Fore.CYAN,
              colorama.Fore.GREEN, colorama.Fore.YELLOW,
              colorama.Fore.BLUE, colorama.Fore.RED]
COLOR_INDEX = 0
iPYTHON_FLAG = 0

LOCAL_IP_ADDRESS = str(check_output(['hostname', '--all-ip-addresses']), encoding = "utf-8").strip(' \n').split('.')


def configure_logger(device_name):
    global COLOR_INDEX
    global iPYTHON_FLAG

    print("==========================================")
    print('Argument List:', str(sys.argv))
    print("==========================================")
# Argument List: ['/Users/liby/Library/Python/3.8/lib/python/site-packages/flask/__main__.py', 'run', '--port=8088']
# Argument List: ['interactive_pyaci.py', '-d', '/dev/tty.usbserial-DN064DB0', '-b', '1000000']
    logger = logging.getLogger(device_name)
    if re.findall("interactive_pyaci.py", str(sys.argv) ) or iPYTHON_FLAG == 1 :
        iPYTHON_FLAG = 1
        logger.setLevel(logging.DEBUG)

        need_pop = 1
        if not logger.handlers:
            need_pop = 0


        stream_formatter = logging.Formatter(
            COLOR_LIST[COLOR_INDEX % len(COLOR_LIST)] + colorama.Style.BRIGHT
            + STREAM_LOG_FORMAT
            + colorama.Style.RESET_ALL)
        COLOR_INDEX = (COLOR_INDEX + 1) % len(COLOR_LIST)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(stream_formatter)
        stream_handler.setLevel(options.log_level)
        logger.addHandler(stream_handler)
        if need_pop == 1:
            print("configure_logger device_name1:" + device_name + " need_pop:" + str(need_pop) + " handlers:" + str(len(logger.handlers)))
            logger.handlers.pop()

        if not options.no_logfile:
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
                print("configure_logger device_name1:" + device_name + " need_pop:" + str(need_pop) + " handlers:" + str(len(logger.handlers)))
                logger.handlers.pop()


    else:
        logger.setLevel(logging.DEBUG)

        need_pop = 1
        if not logger.handlers:
            need_pop = 0


        stream_formatter = logging.Formatter(
            COLOR_LIST[COLOR_INDEX % len(COLOR_LIST)] + colorama.Style.BRIGHT
            + STREAM_LOG_FORMAT
            + colorama.Style.RESET_ALL)
        COLOR_INDEX = (COLOR_INDEX + 1) % len(COLOR_LIST)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(stream_formatter)
        stream_handler.setLevel(logging.DEBUG)
        logger.addHandler(stream_handler)

        if need_pop == 1:
            print("configure_logger device_name2:" + device_name + " need_pop:" + str(need_pop) + " handlers:" + str(len(logger.handlers)))
            logger.handlers.pop()

    print('iPYTHON_FLAG:', str(iPYTHON_FLAG))
    return logger


def updateConfig(name, value):
    """INTERNAL FUNCTION"""
    content = None
    with open(this_file_dir+"/data/config.json", "r+") as confFh:
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
    with open(this_file_dir+"/data/config.json", "w") as confFh:
        confFh.write(json.dumps(confJson))


def getDeviceConfig(name):
    """INTERNAL FUNCTION"""
    with open(this_file_dir+"/data/config.json", "r") as confFh:
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
    DEFAULT_SUBNET_KEY = bytearray([0x4c, 0x53, 0x42, 0x55, 0x45, 0x61, 0x73, 0x79, 0x43, 0x6f, 0x6e, 0x66, 0x59, 0xad, 0x0e, 0x12])
    DEFAULT_VIRTUAL_ADDRESS = bytearray([0xCC] * 16)
    DEFAULT_STATIC_AUTH_DATA = bytearray([0xDD] * 16)
    localUnicastAddr = 0x7fff

    if os.path.isfile(this_file_dir +"/data/config.json"):
        uni = getDeviceConfig("unicastAddress")
        if uni is not False:
            localUnicastAddr = uni

    # if os.path.isfile("data/config.json"):
    #     uni = getDeviceConfig("unicastAddress")
    #     if uni is not False:
    #         localUnicastAddr = uni
        # conf = json.loads(open("data/config.json", "rb").read())
        # if "deviceInfo" in conf and "unicastAddress" in conf["deviceInfo"]:
        #     localUnicastAddr = conf["deviceInfo"]["unicastAddress"]
    DEFAULT_LOCAL_UNICAST_ADDRESS_START = localUnicastAddr

    # CONFIG = ApplicationConfig(
    #     header_path=os.path.join(os.path.dirname(sys.argv[0]),
    #                              ("include/"
    #                               + "nrf_mesh_config_app.h")))
    CONFIG = ApplicationConfig(
        header_path=os.path.join(os.path.split(os.path.realpath(__file__))[0],
                                 ("include/"
                                  + "nrf_mesh_config_app.h")))
    PRINT_ALL_EVENTS = True

    def __init__(self, acidev,myDEFAULT_LOCAL_UNICAST_ADDRESS_START=DEFAULT_LOCAL_UNICAST_ADDRESS_START):
        self.acidev = acidev
        self._event_filter = []
        self._event_filter_enabled = True
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

    def web_import_init(self,new_unicast_address):
        self.DEFAULT_LOCAL_UNICAST_ADDRESS_START = new_unicast_address
        self.local_unicast_address_start = (self.DEFAULT_LOCAL_UNICAST_ADDRESS_START)
        self.access = access.Access(self, self.local_unicast_address_start,
                                    self.CONFIG.ACCESS_ELEMENT_COUNT)
        self.model_add = self.access.model_add

    def reload_setup(self):
        db_path=os.path.join(os.path.split(os.path.realpath(__file__))[0],("database/example_database.json"))
        db = MeshDB(path=db_path)
#        db = MeshDB(path="database/example_database.json")
        self.DEFAULT_SUBNET_KEY = db.net_keys[0].key
        self.DEFAULT_APP_KEY = db.app_keys[0].key
        self.send(cmd.SubnetAdd(0, bytearray(self.DEFAULT_SUBNET_KEY)))
        self.send(cmd.AppkeyAdd(0, 0, bytearray(self.DEFAULT_APP_KEY)))
        self.send(cmd.AddrLocalUnicastSet(
            self.local_unicast_address_start,
            self.CONFIG.ACCESS_ELEMENT_COUNT))

    def __event_handler(self, event):
        global displayMeshMsg
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
            if self.PRINT_ALL_EVENTS and event is not None:
                # 处理client subscription数据
                if isinstance(event, evt.MeshMessageReceivedSubscription):
                    # print("my all event:" + str(event._data))

                    unicast_address = event._data['src']
                    ttl = event._data['ttl']
                    act_length = event._data["actual_length"]
                    data = ['%02x' % b for b in event._data["data"]]
                    msg = ""

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
                        msg = "unicastAddress:" + str(dongleUnicastAddress) \
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
                        msg = "ImprovediBeaconDistance, unicastAddress:" + str(unicast_address) \
                              + ",ttl:" + str(ttl) \
                              + ",majorID:" + str(majorID) \
                              + ",minorID:" + str(minorID) + ",Rssi:" + str(rssi) \
                              + ",ImprovedDistance:" + distance
                    else:
                        self.logger.info(str(event))
                    if msg != '':
                        if displayMeshMsg:
                            self.logger.info(msg)
                self.logger.info(str(event))
            else:
                self._other_events.append(event)


def enableMeshMsgDisplay():
    """开启mesh订阅收到的信息显示"""
    global displayMeshMsg
    displayMeshMsg = True
    print("Display Mesh Msg Enabled!")


def disableMeshMsgDisplay():
    """关闭mesh订阅收到的信息显示"""
    global displayMeshMsg
    displayMeshMsg = False
    print("Display Mesh Msg Disabled!")


def importConfig(dev, configFile=this_file_dir+"/data/LTDMS.json", removeFile=True):
    removeFile = False
    empty_db_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], ("database/example_database.json.backup"))
    db_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], ("database/example_database.json"))
    copy2(empty_db_path, db_path)

    db = MeshDB(path=db_path)
    # db = MeshDB(path="database/example_database.json")

    # 需要先reset()
    if not os.path.isfile(configFile):
        print(this_file_dir+"/data/LTDMS.json NOT EXIST!")
        return False
    conf = json.loads(open(configFile, "r+", encoding='utf-8-sig').read())["MeshInfo"]
    uni = getDeviceConfig("unicastAddress")
    localUnicastAddr = int(conf["provisionedData"]["provisioners"][0]["provisionerAddress"], 16)
    # updateConfig("unicastAddress", min(localUnicastAddr, uni) - 1)


    # 改成寫死 32767 = 7FFF,且不用-1
    # LoaclAddress(provisioner addr) changed by config.ini + ip addr[-1].
    if gl.get_value('MANUAL_CHANGED') is True:
        localUnicastAddr = gl.get_value("PROVISIONERADDRESS") + int(LOCAL_IP_ADDRESS[-1])
        updateConfig("unicastAddress", min(localUnicastAddr, 32767))
    else:
        updateConfig("unicastAddress", min(localUnicastAddr, 32767))


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

    # localaddress如果有設定manual changed的話,就從config.ini新增
    # 就不會從設定檔去讀取local address(provisioner address)
    # below is origin function
    # deviceUnicastAddress = int(provisioners[0]["provisionerAddress"], 16)
    if gl.get_value('MANUAL_CHANGED') is True:
        deviceUnicastAddress = localUnicastAddr
    else:
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
    time.sleep(1.5)
    dev.send(cmd.RadioReset())
    time.sleep(2)
    print("Import Config Complete! Please ReStart Your Machine!")

    if removeFile:
        os.remove(configFile)

    dev.reload_setup()


def start_ipython(options):
    colorama.init()
    comports = options.devices
    d = list()

    # Print out a mini intro to the interactive session --
    # Start with white and then magenta to keep the session white
    # (workaround for a bug in ipython)
    colors = {"c_default": colorama.Fore.WHITE + colorama.Style.BRIGHT,
              "c_highlight": colorama.Fore.YELLOW + colorama.Style.BRIGHT,
              "c_text": colorama.Fore.CYAN + colorama.Style.BRIGHT}

    print(USAGE_STRING.format(**colors))

    if not options.no_logfile and not os.path.exists(LOG_DIR):
        print("Creating log directory: {}".format(os.path.abspath(LOG_DIR)))
        os.mkdir(LOG_DIR)

    for dev_com in comports:
        d.append(Interactive(Uart(port=dev_com,
                                  baudrate=options.baudrate,
                                  device_name=dev_com.split("/")[-1])))

    device = d[0]
    send = device.acidev.write_aci_cmd  # NOQA: Ignore unused variable

    # Set iPython configuration
    ipython_config = traitlets.config.get_config()
    if options.no_logfile:
        ipython_config.TerminalInteractiveShell.logstart = False
        ipython_config.InteractiveShellApp.db_log_output = False
    else:
        dt = DateTime.DateTime()
        logfile = "{}/{}-{}-{}-{}_interactive_session.log".format(
            LOG_DIR, dt.yy(), dt.dayOfYear(), dt.hour(), dt.minute())

        ipython_config.TerminalInteractiveShell.logstart = True
        ipython_config.InteractiveShellApp.db_log_output = True
        ipython_config.TerminalInteractiveShell.logfile = logfile

    ipython_config.TerminalInteractiveShell.confirm_exit = False
    ipython_config.InteractiveShellApp.multiline_history = True
    ipython_config.InteractiveShellApp.log_level = logging.DEBUG

    IPython.embed(config=ipython_config)
    for dev in d:
        dev.close()
    raise SystemExit(0)


def setCurrentVal(gl, currentVal):
    """DT8 EUCI015035BA / EUCI035090BA current setting.
    
    Parameters:
    -----------
		gl : Generic Level Model Instance
        currentVal : uint16_t
            current value:
            EUCI015035BA:254(32767) 219(16383) 183(-1) 146(-32768)
            EUCI035090BA:254(32767) 241(25485) 227(18203) 213(10922) 197(3640)
                        185(-3642) 170(-10924) 156(-18205) 142(-32768)
    """
    if not isinstance(gl, GenericLevelClient):
        print("Invalid gl! It must be an instance of GenericLevelClient!")
    elif not isinstance(currentVal, int):
        print("Invalid Current Value! It must be an int!")
    else:
        val = None
        if currentVal == 254:
            val = 32767
        elif currentVal == 241:
            val = 25485
        elif currentVal == 227:
            val = 18203
        elif currentVal == 219:
            val = 16383
        elif currentVal == 213:
            val = 10922
        elif currentVal == 197:
            val = 3640
        elif currentVal == 185:
            val = -3642
        elif currentVal == 183:
            val = -1
        elif currentVal == 170:
            val = -10924
        elif currentVal == 156:
            val = -18205
        elif currentVal == 146:
            val = -32768
        elif currentVal == 142:
            val = -32768
        if val == None:
            print("Invalid Current Value!")
        else:
            gl.set(val)


def startCommNetwork(dev):
    """Enter Commisioning Network.

    Parameters:
    -----------
        dev : device
    """
    if not isinstance(dev, Interactive):
        print("Invalid dev! It must be an instance of Interactive!")
    else:
        payload = bytearray()
        payload += struct.pack("<B", 1)
        print("Start Advertising Commisioning iBeacon.")
        dev.send(cmd.CommandPacket(0x18, payload))


def stopCommNetwork(dev):
    """Exit Commisioning Network.

    Parameters:
    -----------
        dev : device
    """
    if not isinstance(dev, Interactive):
        print("Invalid dev! It must be an instance of Interactive!")
    else:
        payload = bytearray()
        payload += struct.pack("<B", 0)
        print("Stop Advertising Commisioning iBeacon.")
        dev.send(cmd.CommandPacket(0x18, payload))


def startFtIBeacon(dev, code):
    """Start FT iBeacon Advertising(Serial Cmd).

    Parameters:
    -----------
        dev : device
        code : uint16_t
            code number, 1:On, 2:Off, 3:DIM Up, 4:DIM Down
    """
    if not isinstance(dev, Interactive):
        print("Invalid dev! It must be an instance of Interactive!")
    else:
        payload = bytearray()
        # payload += struct.pack("<BBB", 2, 0x19, code)
        payload += struct.pack("<B", code)
        msg = " Unknown "
        if code == 1:
            msg = " On "
        elif code == 2:
            msg = " Off "
        elif code == 3:
            msg = " DIM Up "
        elif code == 4:
            msg = " DIM Down "
        else:
            print("Invalid code! It should be 1-4!")
            return
        print("Enable Ft iBeacon" + msg + "Advertising.....")
        # payload += struct.pack("<BBB", 2, 0x19, code)
        dev.send(cmd.CommandPacket(0x19, payload))
        # dev.acidev.write_data(payload)


def stopFtIBeacon(dev):
    """Stop FT iBeacon Advertising(Serial Cmd).

    Parameters:
    -----------
        dev : device
    """
    if not isinstance(dev, Interactive):
        print("Invalid dev! It must be an instance of Interactive!")
    else:
        payload = bytearray()
        payload += struct.pack("<B", 0)
        print("Stop Ft iBeacon Advertising.....")
        dev.send(cmd.CommandPacket(0x19, payload))


if __name__ == '__main__':
    global displayMeshMsg
    parser = ArgumentParser(
        description="nRF5 SDK for Mesh Interactive PyACI")
    parser.add_argument("-d", "--device",
                        dest="devices",
                        nargs="+",
                        required=False,
                        default=[gl.get_value('DEV_COM')],
                        help=("Device Communication port, e.g., COM216 or "
                              + "/dev/ttyACM0. You may connect to multiple "
                              + "devices. Separate devices by spaces, e.g., "
                              + "\"-d COM123 COM234\""))
    parser.add_argument("-b", "--baudrate",
                        dest="baudrate",
                        required=False,
                        # default='115200',
                        default=gl.get_value('DEV_BAUDRATE'),
                        help="Baud rate. Default: 1000000")
    parser.add_argument("--no-logfile",
                        dest="no_logfile",
                        action="store_true",
                        required=False,
                        default=False,
                        help="Disables logging to file.")
    parser.add_argument("-l", "--log-level",
                        dest="log_level",
                        type=int,
                        required=False,
                        default=3,
                        help=("Set default logging level: "
                              + "1=Errors only, 2=Warnings, 3=Info, 4=Debug"))
    options = parser.parse_args()

    if options.log_level == 1:
        options.log_level = logging.ERROR
    elif options.log_level == 2:
        options.log_level = logging.WARNING
    elif options.log_level == 3:
        options.log_level = logging.INFO
    else:
        options.log_level = logging.DEBUG
    displayMeshMsg = False
    if sys.platform == 'linux':
        # print("OS: Linux")
        print("OS: Linux, Please open crtscts function. Cmd:stty -F /dev/ttyUSB0 crtscts")
        os.system("stty -F /dev/ttyUSB0 crtscts")

    print("options:"+ str(options))

    start_ipython(options)
