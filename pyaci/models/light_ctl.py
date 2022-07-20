from mesh.access import Model, Opcode
from models.common import TransitionTime
import struct
import time

class LightCTLClient(Model):
    LIGHT_CTL_GET = Opcode(0x825D, None, "Light CTL Get")
    LIGHT_CTL_SET = Opcode(0x825E, None, "Light CTL Set")
    LIGHT_CTL_SET_UNACKNOWLEDGED = Opcode(0x825F, None, "Light CTL Set Unacknowledged")
    LIGHT_CTL_STATUS = Opcode(0x8260, None, "Light CTL Status")

    LIGHT_CTL_TEMPERATURE_GET = Opcode(0x8261, None, "Light CTL Temperature Get")
    LIGHT_CTL_TEMPERATURE_RANGE_GET = Opcode(0x8262, None, "Light CTL Temperature Range Get")
    LIGHT_CTL_TEMPERATURE_RANGE_STATUS = Opcode(0x8263, None, "Light CTL Temperature Range Status")
    LIGHT_CTL_TEMPERATURE_SET = Opcode(0x8264, None, "Light CTL Temperature Set")
    LIGHT_CTL_TEMPERATURE_SET_UNACKNOWLEDGED = Opcode(0x8265, None, "Light CTL Temperature Set Unacknowledged")
    LIGHT_CTL_TEMPERATURE_STATUS = Opcode(0x8266, None, "Light CTL Temperature Status")

    LIGHT_CTL_DEFAULT_GET = Opcode(0x8267, None, "Light CTL Default Get")
    LIGHT_CTL_DEFAULT_STATUS = Opcode(0x8268, None, "Light CTL Default Status")  

    _LIGHT_CTL_DEFAULT_SET                 =   Opcode(0x8269, None, "Light CTL Default Set")
    _LIGHT_CTL_DEFAULT_SET_UNACKNOWLEDGE   =   Opcode(0x826A, None, "Light CTL Default Set Unacknowledged")
    _LIGHT_CTL_TEMPERATURE_Range_SET                 =   Opcode(0x826B, None, "Light CTL Temperature Range Set")
    _LIGHT_CTL_TEMPERATURE_Range_SET_UNACKNOWLEDGE   =   Opcode(0x826C, None, "Light CTL Temperature Range Set Unacknowledged")  

    def __init__(self):
        self.opcodes = [
            (self.LIGHT_CTL_STATUS, self.__light_ctl_status_handler),
            (self.LIGHT_CTL_TEMPERATURE_RANGE_STATUS, self.__light_ctl_temperature_range_status_handler),
            (self.LIGHT_CTL_TEMPERATURE_STATUS, self.__light_ctl_temperature_status_handler),
            (self.LIGHT_CTL_DEFAULT_STATUS, self.__light_ctl_default_status_handler)]
        self.__tid = 0
        super(LightCTLClient, self).__init__(self.opcodes)

    def get(self):
        self.send(self.LIGHT_CTL_GET)
        self.logger.info("Get Light CTL")

    def set(self, lightness, temperature, deltaUV, transition_time_ms=0, delay_ms=0, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<HHHB", lightness, temperature, deltaUV, self._tid)
        if transition_time_ms > 0:
            message += TransitionTime.pack(transition_time_ms, delay_ms)
        if ack:
            self.send(self.LIGHT_CTL_SET, message)
            msg = "Set Light CTL Lightness To " + str(lightness)
            msg += ", Temperature:" + str(temperature)
            msg += ", Delta UV:" + str(deltaUV)
            msg += ", Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.LIGHT_CTL_SET_UNACKNOWLEDGED, message)
                msg = "Set Light CTL Lightness To " + str(lightness)
                msg += " Unacknowledged, Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms, "
                msg += "Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def get_temperature(self):
        self.send(self.LIGHT_CTL_TEMPERATURE_GET)
        self.logger.info("Get Light CTL Temperature")

    def set_temperature(self, temperature, deltaUV, transition_time_ms=0, delay_ms=0, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<HHB", temperature, deltaUV, self._tid)
        if transition_time_ms > 0:
            message += TransitionTime.pack(transition_time_ms, delay_ms)
        if ack:
            self.send(self.LIGHT_CTL_TEMPERATURE_SET, message)
            msg = "Set Light CTL Temperature To " + str(temperature)
            msg += ", Delta UV:" + str(deltaUV)
            msg += ", Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.LIGHT_CTL_TEMPERATURE_SET_UNACKNOWLEDGED, message)
                msg = "Set Light CTL Temperature To " + str(temperature)
                msg += ", Delta UV:" + str(deltaUV)
                msg += " Unacknowledged, Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms, "
                msg += "Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def get_temperature_range(self):
        self.send(self.LIGHT_CTL_TEMPERATURE_RANGE_GET)
        self.logger.info("Get Light CTL Temperature Range")

    def __light_ctl_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light CTL: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 4:
            logstr += " Light CTL Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            present_lightness = int(data[1], 16) << 8 | int(data[0], 16)
            logstr += " Present CTL Lightness: " + str(present_lightness)
            present_temperature = int(data[3], 16) << 8 | int(data[2], 16)
            logstr += " Present CTL Temperature: " + str(present_temperature)
            if dataLength == 9:
                target_lightness = int(data[5], 16) << 8 | int(data[4] ,16)
                logstr += " Target CTL Lightness: " + str(target_lightness)
                target_temperature = int(data[7], 16) << 8 | int(data[6] ,16)
                logstr += " Target CTL Temperature: " + str(target_temperature)
                remaining_time = int(data[8], 16)
                logstr += " Remaining time: %d ms" % (TransitionTime.decode(remaining_time))
            self.logger.info(logstr)

    def __light_ctl_temperature_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light CTL Temperature: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 4:
            logstr += " Light CTL Temperature Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            present_temperature = int(data[1], 16) << 8 | int(data[0], 16)
            logstr += " Present CTL Temperature: " + str(present_temperature)
            present_deltaUV = int(data[3], 16) << 8 | int(data[2], 16)
            logstr += " Present CTL Delta UV: " + str(present_deltaUV)
            if dataLength == 9:
                target_temperature = int(data[5], 16) << 8 | int(data[4] ,16)
                logstr += " Target CTL Temperature: " + str(target_temperature)
                target_deltaUV = int(data[7], 16) << 8 | int(data[6] ,16)
                logstr += " Target CTL Delta UV: " + str(target_deltaUV)
                remaining_time = int(data[8], 16)
                logstr += " Remaining time: %d ms" % (TransitionTime.decode(remaining_time))
            self.logger.info(logstr)
    
    def __light_ctl_temperature_range_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light CTL Temperature  Range: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 2:
            logstr += " Light CTL Temperature Range Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            logstr += " Light CTL Temperature Range " 
            status_code = int(data[0], 16)
            range_min = int(data[2], 16) << 8 | int(data[1], 16)
            range_max = int(data[4], 16) << 8 | int(data[3], 16)
            status_msg = " Unknown "
            if status_code == 0x00:
                status_msg = " Success "
            elif status_code == 0x01:
                status_msg = " Cannot Set Range Min "
            elif status_code == 0x01:
                status_msg = " Cannot Set Range Max "
            else:
                status_msg = " RFU "
            logstr += status_msg
            logstr += " Range Min: " + str(range_min)
            logstr += " Range Max: " + str(range_max)
            self.logger.info(logstr)
    
    def __light_ctl_default_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light CTL Default: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 6:
            logstr += " Light CTL Default Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            lightness = int(data[1], 16) << 8 | int(data[0], 16)
            logstr += " Light CTL Default Lightness: " + str(lightness)
            temperature = int(data[3], 16) << 8 | int(data[2], 16)
            logstr += " Light CTL Default Temperature: " + str(temperature)
            deltaUV = int(data[5], 16) << 8 | int(data[4], 16)
            logstr += " Light CTL Default Delta UV: " + str(deltaUV)
            self.logger.info(logstr)

    def set_default(self, lightness, temperature, deltaUV, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<HHH", lightness, temperature, deltaUV)
        msg = "Light CTL Default Set" + ("" if ack else " Unacknowledged") + ":"
        msg += " lightness:" + str(lightness)
        msg += " temperature:" + str(temperature)
        msg += " deltaUV:" + str(deltaUV)
        if ack:
            self.send(self._LIGHT_CTL_DEFAULT_SET, message)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self._LIGHT_CTL_DEFAULT_SET_UNACKNOWLEDGE, message)
                self.logger.info(msg + " repeat:" + str(i))
                i -= 1

    def set_temperature_range(self, range_min, range_max, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<HH", range_min, range_max)
        msg = "Light CTL Temperature Range Set" + ("" if ack else " Unacknowledged") + ":"
        msg += " range min:" + str(range_min)
        msg += " range max:" + str(range_max)
        if ack:
            self.send(self._LIGHT_CTL_TEMPERATURE_Range_SET, message)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self._LIGHT_CTL_TEMPERATURE_Range_SET_UNACKNOWLEDGE, message)
                self.logger.info(msg + " repeat:" + str(i))
                i -= 1
    
    @property
    def _tid(self):
        tid = self.__tid
        self.__tid += 1
        if self.__tid >= 255:
            self.__tid = 0
        return tid