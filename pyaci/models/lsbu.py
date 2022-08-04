from mesh.access import Model, Opcode
from models.common import TransitionTime
import struct
import datetime
import time
import re
from mesh.database import MeshDB
import json
import os
from mesh import types as mt                            # NOQA: ignore unused import


class LsbuClient(Model):
    _LSBU_SETTING_SET       = Opcode(0xC0, 0x069E, "Delta LSBU Set")
    _LSBU_SETTING_GET       = Opcode(0xC1, 0x069E, "Delta LSBU Get")
    _LSBU_SETTING_STATUS    = Opcode(0xC2, 0x069E, "Delta LSBU Status")
    _LSBU_RESET_TO_FACTORY  = Opcode(0xC7, 0x069E, "Delta LSBU Reset To Factory")
    _LSBU_ENTER_DFU_MODE    = Opcode(0xC8, 0x069E, "Delta LSBU Enter DFU Mode")
    _LSBU_FDT_DFU_STATUS    = Opcode(0xC9, 0x069E, "Delta LSBU FDT DFU Status")

    # _LSBU_EZCONFIG_REQUEST_PUBLISH                  = Opcode(0xCA, 0x069E, "Delta LSBU EzConfig Request Publish")
    _LSBU_EZCONFIG_REQUEST_PUBLISH_STATUS           = Opcode(0xCB, 0x069E, "Delta LSBU EzConfig Request Publish Status")
    # _LSBU_SW3_SCENE_NUMBER_SET                    = Opcode(0xCD, 0x069E, "Delta LSBU SW3 Scene Number Set")
    # _LSBU_SW3_SCENE_NUMBER_GET                    = Opcode(0xCE, 0x069E, "Delta LSBU SW3 Scene Number Get")
    # _LSBU_SW3_SCENE_NUMBER_STATUS                 = Opcode(0xCF, 0x069E, "Delta LSBU SW3 Scene Number Status")
    # _LSBU_EZCONFIG_GROUP_SUBSCRIBE_STATUS         = Opcode(0xD0, 0x069E, "Delta LSBU EzConfig Group Subscribe Status")
    _LSBU_EZCONFIG_REQUEST_COMPOSITION_DATA         = Opcode(0xD1, 0x069E, "Delta LSBU EzConfig Request Composition Data")
    _LSBU_EZCONFIG_REQUEST_COMPOSITION_DATA_STATUS  = Opcode(0xD2, 0x069E, "Delta LSBU EzConfig Request Composition Data Status")
    _LSBU_SET_TIME_PERIOD_OF_ENERGY_LOG_DATA        = Opcode(0xD5, 0x069E, "Delta LSBU energy log Data")
    _LSBU_ENERGY_LOG_DATA_STATUS                    = Opcode(0xD6, 0x069E, "Delta LSBU energy log Data status")


    def __init__(self):
        self.opcodes = [
            (self._LSBU_SETTING_STATUS,  self.__lsbu_setting_status_handler),
            (self._LSBU_FDT_DFU_STATUS,  self.__lsbu_fdt_dfu_status_handler),
            (self._LSBU_EZCONFIG_REQUEST_PUBLISH_STATUS,  self.__lsbu_ezconfig_request_publish_status_handler),
            # (self._LSBU_EZCONFIG_GROUP_SUBSCRIBE_STATUS,  self.__lsbu_ezconfig_group_subscribe_status_handler),
            (self._LSBU_EZCONFIG_REQUEST_COMPOSITION_DATA_STATUS,  self.__lsbu_ezconfig_request_composition_data_status_handler),
            (self._LSBU_ENERGY_LOG_DATA_STATUS,  self.__lsbu_energy_log_data_status_handler)]

        self.__isDFUReset = ""
        # cesar 20190827 记录本次操作nodeUUID 用于恢复出厂设置与进入DFU模式
        self.nodeUUID = ""
        self.nodeName = ""
        self.isReset = False
        self.deviceId = []
        self.deviceAddress = []
        super(LsbuClient, self).__init__(self.opcodes)

        self.last_cmd_resp_dict = {}
        self.devicePublishInfoDict = {}
        self.deviceMaxPowerRatioDict = {}

        self.callback_energy_log = None

    def __lsbu_ezconfig_request_publish_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        devicePublishInfoDict = {}
        devicePublishInfoDict['productId'] = message.data[1] * 256 + message.data[0]
        devicePublishInfoDict['VersionId'] = message.data[3] * 256 + message.data[2]
        devicePublishInfoDict['fwVersion'] = message.data[7] | message.data[6] >> 2 | message.data[5] >> 4 | message.data[4] >> 6

        logstr = "Source Address: " + str(dongleUnicastAddress)
        logstr += ", ProductId:" + str(message.data[1] * 256 + message.data[0])
        logstr += ", VersionId:" + str(message.data[3] * 256 + message.data[2])
        self.logger.info(logstr)

    #todo
    def __lsbu_energy_log_data_status_handler(self, opcode, message):
        self.logger.info(str(message))
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data

        dataLen = len(data)
        if dataLen >= 4:
            resp = bytearray([data[1], data[0]])
            resp += data[2:]
        else:
            resp = data
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # Multiple hours data
        bData = message.data[::-1]

        hoursData = {}
        hoursData[str(dongleUnicastAddress)] = {}
        hoursData[str(dongleUnicastAddress)]['hours'] = {}
        hoursData[str(dongleUnicastAddress)]['hours']['byte'] = {}
        hoursData[str(dongleUnicastAddress)]['hours']['value'] = {}

        hours = int(dataLength / 4)
        j = int(dataLength / 4 - 1)
        for i in range(0, dataLength, 4):
            hoursData[str(dongleUnicastAddress)]['hours']['byte'][str(j)] = bData[i : 4+i]
            hoursData[str(dongleUnicastAddress)]['hours']['value'][str(j)] = int.from_bytes(hoursData[str(dongleUnicastAddress)]['hours']['byte'][str(j)], byteorder='big')
            j -= 1


        if message is None or message.data is None:
            logstr += " Lsbu Setting Status: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 4:
            logstr += " Lsbu Setting Status Error: msg="
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            logstr += " Lsbu Setting Status: "
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
            self.last_cmd_resp_dict[str(message.meta['src'])+"Energy"] = hoursData


            self.callback_energy_log(dongleUnicastAddress, hours, hoursData, self.devicePublishInfoDict, self.deviceMaxPowerRatioDict)



    def requestCompositionData(self, resp_times):
        if not isinstance(resp_times, int):
            print("Invalid resp_times! It must be an int!")
        else:
            message = bytearray()
            message += struct.pack("<B", resp_times)
            msg = "LSBU Model Request Composition Data, Response Times:" + ('%02x' % resp_times)
            self.logger.info(msg)
            self.send(self._LSBU_EZCONFIG_REQUEST_COMPOSITION_DATA, message)

    def __lsbu_ezconfig_request_composition_data_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        logstr += ", ProductId:" + str(message.data[1] * 256 + message.data[0])
        logstr += ", VersionId:" + str(message.data[3] * 256 + message.data[2])
        logstr += ", FW_Version:" + str(message.data[7]) + "." + str(message.data[6]) + "." + str(message.data[5]) + "." + str(message.data[4])

        self.devicePublishInfoDict[str(dongleUnicastAddress)] = {}
        self.devicePublishInfoDict[str(dongleUnicastAddress)]['productId'] = message.data[1] * 256 + message.data[0]
        self.devicePublishInfoDict[str(dongleUnicastAddress)]['VersionId'] = message.data[3] * 256 + message.data[2]
        self.devicePublishInfoDict[str(dongleUnicastAddress)]['fwVersion'] = int(str(message.data[7]) + str(message.data[6]) + str(message.data[5]) + str(message.data[4]))
        self.last_cmd_resp_dict[str(message.meta['src']) + "compositionData"] = self.devicePublishInfoDict
        self.logger.info(logstr)

    def settingGet(self, propertyID):
        message = bytearray()
        message += struct.pack("<H", propertyID)
        self.send(self._LSBU_SETTING_GET, message)
        msg = "LSBU Model Setting Get: PropertyID:0x" + ('%02x' % propertyID)
        self.logger.info(msg)

    def settingSet(self, propertyID, dataSize, settingValue):
        isValid = True
        message = bytearray()
        errMsg = ""
        if propertyID == 0x0001 and dataSize == 1:
            if settingValue != 0 and settingValue != 1:
                isValid = False
                errMsg = "LSBU Model Setting Set Error: Setting Value ERROR!"
            else:
                message += struct.pack("<HBB", propertyID, dataSize, settingValue)
        elif propertyID == 0x0002 and dataSize == 8:
            settingVal = re.findall('.{2}', settingValue)
            if len(settingVal) == 8:
                message += struct.pack("<HB", propertyID, dataSize)
                message += bytearray(int(x, 16) for x in settingVal)
            else:
                isValid = False
                errMsg = "LSBU Model Setting Set Error: Setting Value Length ERROR!"
        elif propertyID == 0x0003 and dataSize == 1:
            if settingValue != 0x04 and settingValue != 0x03 and settingValue != 0x00 \
             and settingValue != 0xFC and settingValue != 0xF8 and settingValue != 0xF4 \
              and settingValue != 0xF0 and settingValue != 0xEC and settingValue != 0xDB:
                isValid = False
                errMsg = "Setting Value ERROR!"
            else:
                message += struct.pack("<HBB", propertyID, dataSize, settingValue)
        elif propertyID == 0x0013 and dataSize == 2:
            message += struct.pack("<HBH", propertyID, dataSize, settingValue)
        elif propertyID == 0x0014 and dataSize == 4:
            settingVal = re.findall('.{2}', settingValue)
            message += struct.pack("<HB", propertyID, dataSize)
            message += bytearray(int(x, 16) for x in settingVal)
        elif propertyID == 0x0015 and dataSize == 1:
            message += struct.pack("<HBB", propertyID, dataSize, settingValue)
        elif propertyID in [0x0017, 0x0018] and dataSize == 2:
            message += struct.pack("<HBH", propertyID, dataSize, settingValue)
        else:
            isValid = False
            errMsg = "LSBU Model Setting Set Error: Setting Cmd or Size ERROR!"
            
        if isValid:
            msg = "LSBU Model Setting Set: PropertyID:0x" + ('%02x' % propertyID)
            msg += " Data Size:" + ('%02x' % dataSize)
            msg += " Setting Value:" + (('%02x' % settingValue) if isinstance(settingValue, int) else settingValue)
            # msg += " Setting Value:" + (('%02x' % settingValue) if dataSize == 1 else settingValue)
            self.logger.info(msg)

            self.send(self._LSBU_SETTING_SET, message)
        else:
            self.logger.info("setting set/get message ERROR:" + errMsg)

    def set(self, propertyID, settingValue, transition_time_ms, repeat):
        isValid = True
        message = bytearray()
        errMsg = ""
        if settingValue < 0:
            isValid = False
            errMsg = "LSBU Model Setting Set Error: Setting Value ERROR!"
        # set time period
        # B is an unsigned char, 1 byte, value range: 0 to 255
        # H is an unsigned short, 2 bytes, value range: 0 to 65535
        elif propertyID == 0xd5:
            message += struct.pack("<B", settingValue)
        else:
            isValid = False
            errMsg = "LSBU Model Setting Set Error: Setting Cmd or Size ERROR!"

        if isValid:
            msg = "LSBU Model Setting Set: PropertyID:0x" + ('%02x' % propertyID)
            msg += " Setting Value:" + (('%02x' % settingValue) if isinstance(settingValue, int) else settingValue)
            # msg += " Setting Value:" + (('%02x' % settingValue) if dataSize == 1 else settingValue)
            self.logger.info(msg)

        i = repeat
        while i > 0:
            time.sleep(0.5)
            self.send(self._LSBU_SET_TIME_PERIOD_OF_ENERGY_LOG_DATA, message)
            msg += "Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Repeat:" + str(i)
            self.logger.info(msg)
            i -= 1


    def __lsbu_setting_status_handler(self, opcode, message):
        self.logger.info(str(message))
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        if dataLen >= 4:
            resp = bytearray([data[1], data[0]])
            resp += data[2:]
        else:
            resp = data
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)
        if message is None or message.data is None:
            logstr += " Lsbu Setting Status: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 4:
            logstr += " Lsbu Setting Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            logstr += " Lsbu Setting Status: "
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
            if data[0] == "02":
                # self.deviceID = ''.join(['%02x' % b for b in message.data[3:]])
                self.deviceId = data[3:]
            elif data[0] == "12":
                # self.deviceAddress = ''.join(['%02x' % b for b in message.data[3:]])
                self.deviceAddress = data[3:]
            elif data[0] == "17":
                # 快速添加群组
                groupNames = []
                groupAddress = int(data[4] + data[3], 16)
                # 生成node name
                isDuplicate = False
                for g in self.db.groups:
                    groupNames.append(g.name)
                    if groupAddress == g.address:
                        isDuplicate = True
                        break
                if isDuplicate:
                    print("Add Group 0x" + data[4] + data[3] + " Failed!")
                else:
                    i = 1
                    groupNameTmp = 'Group '
                    while groupNameTmp + str(i) in groupNames:
                        i += 1
                    groupName = groupNameTmp + str(i)
                    
                    self.db.groups.append(mt.Group(groupName, groupAddress, 0))    
                    self.db.store()
                    print("Add Group 0x" + data[4] + data[3] + " Success!")
            elif data[0] == "18":
                # 快速删除群组
                groupAddress = int(data[4] + data[3], 16)
                isDeleted = False
                for g in self.db.groups:
                    if groupAddress == g.address:
                        self.db.groups.remove(g)
                        self.db.store()
                        isDeleted = True
                        break
                print("Delete Group 0x" + data[4] + data[3] + (" Success!" if isDeleted else " Failed!"))
            # Max mA and Power
            elif data[0] == "06":
                bRatio = message.data[3] & 0x7f
                self.deviceMaxPowerRatioDict[str(dongleUnicastAddress)] = bRatio
                self.last_cmd_resp_dict[str(message.meta['src']) + "PowerRatio"] = self.deviceMaxPowerRatioDict




    def resetToFactory(self, deviceID):
        isValid = True
        message = bytearray()
        deviceIDVal = re.findall('.{2}', deviceID)
        # if len(deviceIDVal) == 8 and (self.nodeUUID != '' or self.nodeName != ''):
        if len(deviceIDVal) == 8:
            message = bytearray(int(x, 16) for x in deviceIDVal)
        else:
            isValid = False
            
        if isValid:
            m = "".join(['%02x' % b for b in message])
            self.logger.info("reset to factory set message:" + m)
            self.send(self._LSBU_RESET_TO_FACTORY, message)
            self.__isDFUReset = "reset"
        else:
            # self.logger.info("reset to factory message ERROR:" + ("DeviceID Length Error" if self.nodeUUID!='' or self.nodeName!='' else "Please Change to Target Node"))
            self.logger.info("reset to factory message Failed!")


    def enterDfuMode(self, deviceID):
        isValid = True
        message = bytearray()
        deviceIDVal = re.findall('.{2}', deviceID)
        # deviceIDVal.reverse()
        # if len(deviceIDVal) == 8 and self.nodeUUID != '' or self.nodeName != '':
        if len(deviceIDVal) == 8:
            message = bytearray(int(x, 16) for x in deviceIDVal)
        else:
            isValid = False
            
        if isValid:
            m = "".join(['%02x' % b for b in message])
            self.logger.info("enter dfu mode message:" + m)
            self.send(self._LSBU_ENTER_DFU_MODE, message)
            self.__isDFUReset = "dfu"
        else:
            # self.logger.info("enter dfu mode message ERROR:" + ("DeviceID Length Error" if self.nodeUUID!='' or self.nodeName!='' else "Please Change to Target Node"))
            self.logger.info("enter dfu mode message Failed!")
        
    def __lsbu_fdt_dfu_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)
        if message is None or message.data is None:
            logstr += " Lsbu fdt dfu Status: message is None!!"
            self.logger.info(logstr)
        elif dataLength != 1:
            logstr += " Lsbu fdt dfu Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            logstr += " Lsbu fdt dfu Status: "
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
            # 为了再次provision时reset target node，否则会占用devkey handle8，address handle0
            self.isReset = True
            # # RESET 删除数据库
            # if self.__isDFUReset == "reset":
            #     for n in self.db.nodes:
            #         if self.nodeName != '' and n.name == self.nodeName:
            #             self.db.nodes.remove(n)
            #             self.db.store()
            #             # self.__resetTargetNode()
            #             break
            # # 进入DFU模式    存储到文件   后续resume
            # elif self.__isDFUReset == "dfu":
            #     for n in self.db.nodes:
            #         nodeNameKey = n.name.replace(' ', '%20')
            #         if self.nodeName != '' and n.name == self.nodeName:
            #             resumeNodeFile = "data/resumeNode.json"
            #             if os.path.isfile(resumeNodeFile) and os.path.getsize(resumeNodeFile) > 0:
            #                 resumeNodes = json.loads(open(resumeNodeFile, "r").read())
            #                 resumeNodes[nodeNameKey] = n
            #                 open(resumeNodeFile, "w+").write(json.dumps(resumeNodes))
            #             else:
            #                 open(resumeNodeFile, "w+").write(json.dumps({nodeNameKey:n}))

            #             # if os.path.isdir(sourceFile):
            #             #     First_Directory = False
            #             #     copyFiles(sourceFile, targetFile)
            #             #     print("Database Reset OK!")

            #             # open("data/resumeNode.json", "wb").write(n)
            #             self.db.nodes.remove(n)
            #             self.db.store()
            #             # self.__resetTargetNode()
            #             break

    def set_callback_energy_log(self, callback):
        self.callback_energy_log = callback