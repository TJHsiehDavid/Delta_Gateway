
from mesh.access import Model, Opcode
from models.common import TransitionTime
import struct
import time

class LightLCClient(Model):
    LIGHT_LC_MODE_GET = Opcode(0x8291, None, "Light LC Mode Get")
    LIGHT_LC_MODE_SET = Opcode(0x8292, None, "Light LC Mode Set")
    LIGHT_LC_MODE_SET_UNACKNOWLEDGED = Opcode(0x8293, None, "Light LC Mode Set Unacknowledged")
    LIGHT_LC_MODE_STATUS = Opcode(0x8294, None, "Light LC Mode Status")

    LIGHT_LC_OM_GET = Opcode(0x8295, None, "Light LC OM Get")
    LIGHT_LC_OM_SET = Opcode(0x8296, None, "Light LC OM Set")
    LIGHT_LC_OM_SET_UNACKNOWLEDGED = Opcode(0x8297, None, "Light LC OM Set Unacknowledged")
    LIGHT_LC_OM_STATUS = Opcode(0x8298, None, "Light LC OM Status")

    LIGHT_LC_ONOFF_GET = Opcode(0x8299, None, "Light LC OnOff Get")
    LIGHT_LC_ONOFF_SET = Opcode(0x829A, None, "Light LC OnOff Set")
    LIGHT_LC_ONOFF_SET_UNACKNOWLEDGED = Opcode(0x829B, None, "Light LC OnOff Set Unacknowledged")
    LIGHT_LC_ONOFF_STATUS = Opcode(0x829C, None, "Light LC OnOff Status")

    LIGHT_LC_PROPERTY_GET = Opcode(0x829D, None, "Light LC Property Get")
    LIGHT_LC_PROPERTY_SET = Opcode(0x62, None, "Light LC Property Set")
    LIGHT_LC_PROPERTY_SET_UNACKNOWLEDGED = Opcode(0x63, None, "Light LC Property Set Unacknowledged")
    LIGHT_LC_PROPERTY_STATUS = Opcode(0x64, None, "Light LC Property Status")   

    def __init__(self):
        self.opcodes = [
            (self.LIGHT_LC_MODE_STATUS, self.__light_lc_mode_status_handler),
            (self.LIGHT_LC_OM_STATUS, self.__light_lc_om_status_handler),
            (self.LIGHT_LC_ONOFF_STATUS, self.__light_lc_onoff_status_handler),
            (self.LIGHT_LC_PROPERTY_STATUS, self.__light_lc_property_status_handler)]
        self.__tid = 0
        super(LightLCClient, self).__init__(self.opcodes)

    def get_mode(self):
        self.send(self.LIGHT_LC_MODE_GET)
        self.logger.info("Get Light LC Mode")

    def set_mode(self, mode, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<B", mode)
        if mode not in [0b0, 0b1]:
            self.logger.info("Mode Error! MUST BE 0 or 1!")
            return
        msg = "Set Light LC Mode To " + str(mode)
        if mode == 0b0:
            msg += " (The controller is turned off. The binding with the Light Lightness state is disabled.)"
        else:
            msg += " (The controller is turned on. The binding with the Light Lightness state is enabled.)"
        if ack:
            self.send(self.LIGHT_LC_MODE_SET, message)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.LIGHT_LC_MODE_SET_UNACKNOWLEDGED, message)
                msg += " Unacknowledged, Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def get_om(self):
        self.send(self.LIGHT_LC_OM_GET)
        self.logger.info("Get Light LC Occupany Mode")

    def set_om(self, mode, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<B", mode)
        if mode not in [0b0, 0b1]:
            self.logger.info("Mode Error! MUST BE 0 or 1!")
            return
        msg = "Set Light LC Occupany Mode To " + str(mode)
        if mode == 0b0:
            msg += " (Off or Standby)"
        else:
            msg += " (Occupancy or Run or Prolong)"
        if ack:
            self.send(self.LIGHT_LC_OM_SET, message)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.LIGHT_LC_OM_SET_UNACKNOWLEDGED, message)
                msg += " Unacknowledged, Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def get_onoff(self):
        self.send(self.LIGHT_LC_ONOFF_GET)
        self.logger.info("Get Light LC OnOff")

    def set_onoff(self, onoff, transition_time_ms=0, delay_ms=0, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<BB", onoff, self._tid)
        if mode not in [0b0, 0b1]:
            self.logger.info("OnOff Error! MUST BE 0 or 1!")
            return
        if transition_time_ms > 0:
            message += TransitionTime.pack(transition_time_ms, delay_ms)
        onoff_msg = str(onoff)
        if onoff == 0:
            onoff_msg += "(off)"
        else:
            onoff_msg += "(on)"
        if ack:
            self.send(self.LIGHT_LC_ONOFF_SET, message)
            msg = "Set Light LC Light OnOff To " + onoff_msg
            msg += ", Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.LIGHT_LC_ONOFF_SET_UNACKNOWLEDGED, message)
                msg = "Set Light LC Light OnOff To " + onoff_msg
                msg += " Unacknowledged, Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms, "
                msg += "Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def get_property(self, propertyID):
        message = bytearray()
        message += struct.pack("<H", propertyID)
        self.send(self.LIGHT_LC_PROPERTY_GET, message)
        self.logger.info("Get Light LC Property")

    def set_property(self, propertyID, propertyVal, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<H", propertyID)
        message += bytearray(int(x, 16) for x in propertyVal)
        msg = "Set Light LC Property" + ("" if ack else " Unacknowledged")
        msg += ", PropertyID:" + str(propertyID)
        msg += ", PropertyVal:" + str(propertyVal)
        if ack:
            self.send(self.LIGHT_LC_PROPERTY_SET, message)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.LIGHT_LC_PROPERTY_SET_UNACKNOWLEDGED, message)
                msg += ", Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def __light_lc_mode_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        if message is None or message.data is None:
            logstr += " Light LC Mode: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 4:
            logstr += " Light LC Mode Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            mode = int(data[0], 16)
            logstr += " Light LC Mode:"
            logstr += str(mode)
            if mode == 0b0:
                logstr += " (The controller is turned off. The binding with the Light Lightness state is disabled.)"
            else:
                logstr += " (The controller is turned on. The binding with the Light Lightness state is enabled.)"
            self.logger.info(logstr)

    def __light_lc_om_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        if message is None or message.data is None:
            logstr += " Light LC Occupany Mode: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 4:
            logstr += " Light LC Occupany Mode Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            mode = int(data[0], 16)
            logstr += " Light LC Occupany Mode:"
            logstr += str(mode)
            if mode == 0b0:
                logstr += " (Off or Standby)"
            else:
                logstr += " (Occupancy or Run or Prolong)"
            self.logger.info(logstr)
    
    def __light_lc_onoff_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)
        if message is None or message.data is None:
            logstr += " Light LC Light OnOff: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 1:
            logstr += " Light LC Light OnOff Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            present_onoff = int(data[0], 16)
            target_onoff = int(data[1], 16)
            remaining_time = int(data[2], 16)
            logstr += " Light LC Light OnOff "
            logstr += " Present OnOff: " + ("on " if present_onoff == 1 else "off ")
            if len(message.data) >= 2:
                logstr += " Target OnOff: " + ("on " if target_onoff == 1 else "off ")
                logstr += " Remaining time: %d ms" % (TransitionTime.decode(remaining_time))
            self.logger.info(logstr)
    
    def __light_lc_property_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light LC Property: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 3:
            logstr += " Light LC Property Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            propertyID = int(data[1], 16) << 8 | int(data[0], 16)
            logstr += " Light LC PropertyID:0x" + hex(propertyID)
            logstr += " PropertyVal: 0x" + ''.join(["%02x" % b for b in data[2:]])
            self.logger.info(logstr)
    
    @property
    def _tid(self):
        tid = self.__tid
        self.__tid += 1
        if self.__tid >= 255:
            self.__tid = 0
        return tid