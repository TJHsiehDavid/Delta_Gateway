from mesh.access import Model, Opcode
from models.common import TransitionTime
import struct
import datetime
import time


class SceneClient(Model):
    _SCENE_GET                      =   Opcode(0x8241, None, "Scene Get")
    _SCENE_RECALL                   =   Opcode(0x8242, None, "Scene Recall")
    _SCENE_RECALL_UNACKNOWLEDGED    =   Opcode(0x8243, None, "Scene Recall Unacknowledged")
    _SCENE_STATUS                   =   Opcode(0x5E,   None, "Scene Status")
    _SCENE_REGISTER_GET             =   Opcode(0x8244, None, "Scene Register Get")
    _SCENE_REGISTER_STATUS          =   Opcode(0x8245, None, "Scene Register Status")
    _SCENE_STORE                        =   Opcode(0x8246, None, "Scene Store")
    _SCENE_STORE_UNACKNOWLEDGED         =   Opcode(0x8247, None, "Scene Store Unacknowledged")
    _SCENE_DELETE                       =   Opcode(0x829E, None, "Scene Delete")
    _SCENE_DELETE_UNACKNOWLEDGED        =   Opcode(0x829F, None, "Scene Delete Unacknowledged")

    def __init__(self):
        self.opcodes = [
            (self._SCENE_STATUS                 , self.__scene_status_handler),
            (self._SCENE_REGISTER_STATUS        , self.__scene_register_status_handler)]
        self.__tid = 0
        self.__status_codes_val = [0, 1, 2]
        self.__status_codes = ["Success", "Scene Register Full", "Scene Not Found"]
        self.last_cmd_resp_dict = {}
        super(SceneClient, self).__init__(self.opcodes)

    def sceneGet(self):
        self.send(self._SCENE_GET)
        msg = "Scene Get"
        self.logger.info(msg)

    def sceneRecall(self, sceneNumber, transition_time_ms=0, delay_ms=0, ack=False, repeat=1):
        message = bytearray()
        message += struct.pack("<HB", sceneNumber, self._tid)
        ##if transition_time_ms > 0:
        message += TransitionTime.pack(transition_time_ms, delay_ms)
        if ack:
            self.send(self._SCENE_RECALL, message)
            msg = " Recall Scene " + str(sceneNumber)
            msg += ", Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self._SCENE_RECALL_UNACKNOWLEDGED, message)
                msg = " Recall Scene " + str(sceneNumber) + " Unacknowledged"
                msg += ", Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms"
                self.logger.info(msg)
                i -= 1
    @property
    def _tid(self):
        tid = self.__tid
        self.__tid += 1
        if self.__tid >= 255:
            self.__tid = 0
        return tid               
    def sceneRegisterGet(self):
        self.send(self._SCENE_REGISTER_GET)
        msg = "Scene Register Get"
        self.logger.info(msg)

    def __scene_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        if dataLen == 3:
            resp = bytearray([data[0], data[2], data[1]])
        elif dataLen == 5:
            resp = bytearray([data[0], data[2], data[1], data[4], data[3]])
        elif dataLen == 6:
            resp = bytearray([data[0], data[2], data[1], data[4], data[3], data[5]])
        else:
            resp = data
        dataLength = len(message.data)
        data = message.data
        if message is None or message.data is None:
            logstr += " Scene Status: message is None!!"
        elif dataLength < 3:
            logstr += " Scene Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
        else:
            self.last_cmd_resp_dict[SceneClient._SCENE_STATUS.opcode] = message.data
            logstr += " Scene Status: "
            logstr += self.__status_codes[data[0]] if (data[0] in self.__status_codes_val) else "Unknown"
            logstr += ",Current Scene:" + str(data[1] + data[2] *256)
            if dataLength == 6:
                logstr += ",Target Scene:" + str(data[3] + data[4] *256) + ","
                logstr += " Remaining time: %d ms" % (TransitionTime.decode(data[5]))
        self.logger.info(logstr)
        
    def __scene_register_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        # 00 0300 0100 0200 0300
        dataLen = len(data)
        if dataLen == 35:
            resp = bytearray([data[0], data[2], data[1]])
            #0100 0200 0300
            scenes = data[3:]
            i = 0
            while i < 16:
                resp += bytearray([scenes[i * 2 + 1], scenes[i * 2]])
                i += 1
        else:
            resp = data
        dataLength = len(message.data)
        data = message.data
        if message is None or message.data is None:
            logstr += " Scene Register Status: message is None!!"
        elif dataLength < 3:
            logstr += " Scene Register Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
        else:
            logstr += " Scene Register Status: "
            logstr += self.__status_codes[data[0]] if (data[0] in self.__status_codes_val) else "Unknown"
            logstr += ",Current Scene:" + str(data[1] + data[2] *256) + ","
            scenes = data[3:]
            sceneCount = 0
            sceneListStr = ",Scenes List:"
            i = 0
            while i < 16:
                sceneNumber = scenes[2*i] + scenes[2*i+1] * 256
                if sceneNumber > 0:
                    sceneListStr += str(sceneNumber) + " "
                    sceneCount += 1
                i += 1
            logstr += " Scenes Count:" + str(sceneCount)
            if sceneCount > 0:
                logstr += sceneListStr
        self.logger.info(logstr)

        
    def sceneStore(self, sceneNumber, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<H", sceneNumber)
        if ack:
            self.send(self._SCENE_STORE, message)
            msg = "Store Scene " + str(sceneNumber)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self._SCENE_STORE_UNACKNOWLEDGED, message)
                msg = "Store Scene " + str(sceneNumber) + " Unacknowledged"
                self.logger.info(msg)
                i -= 1

    def sceneDelete(self, sceneNumber, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<H", sceneNumber)
        if ack:
            self.send(self._SCENE_DELETE, message)
            msg = "Store Scene " + str(sceneNumber)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self._SCENE_DELETE_UNACKNOWLEDGED, message)
                msg = "Delete Scene " + str(sceneNumber) + " Unacknowledged"
                self.logger.info(msg)
                i -= 1
