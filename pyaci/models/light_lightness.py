from mesh.access import Model, Opcode
from models.common import TransitionTime
import struct
import time

class LightLightnessClient(Model):
    LIGHT_LIGHTNESS_GET = Opcode(0x824B, None, "Light Lightness Get")
    LIGHT_LIGHTNESS_SET = Opcode(0x824C, None, "Light Lightness Set")
    LIGHT_LIGHTNESS_SET_UNACKNOWLEDGED = Opcode(0x824D, None, "Light Lightness Set Unacknowledged")
    LIGHT_LIGHTNESS_STATUS = Opcode(0x824E, None, "Light Lightness Status")

    LIGHT_LIGHTNESS_LINEAR_GET = Opcode(0x824F, None, "Light Lightness Linear Get")
    LIGHT_LIGHTNESS_LINEAR_SET = Opcode(0x8250, None, "Light Lightness Linear Set")
    LIGHT_LIGHTNESS_LINEAR_SET_UNACKNOWLEDGED = Opcode(0x8251, None, "Light Lightness Linear Set Unacknowledged")
    LIGHT_LIGHTNESS_LINEAR_STATUS = Opcode(0x8252, None, "Light Lightness Linear Status")

    LIGHT_LIGHTNESS_LAST_GET = Opcode(0x8253, None, "Light Lightness Last Get")
    LIGHT_LIGHTNESS_LAST_STATUS = Opcode(0x8254, None, "Light Lightness Last Status")

    LIGHT_LIGHTNESS_DEFAULT_GET = Opcode(0x8255, None, "Light Lightness Default Get")
    LIGHT_LIGHTNESS_DEFAULT_STATUS = Opcode(0x8256, None, "Light Lightness Default Status")

    LIGHT_LIGHTNESS_RANGE_GET = Opcode(0x8257, None, "Light Lightness Range Get")
    LIGHT_LIGHTNESS_RANGE_STATUS = Opcode(0x8258, None, "Light Lightness Range Status")

    _LIGHT_LIGHTNESS_DEFAULT_SET                 =   Opcode(0x8259, None, "Light Lightness Default Set")
    _LIGHT_LIGHTNESS_DEFAULT_SET_UNACKNOWLEDGE   =   Opcode(0x825A, None, "Light Lightness Default Set Unacknowledged")
    _LIGHT_LIGHTNESS_Range_SET                 =   Opcode(0x825B, None, "Light Lightness Range Set")
    _LIGHT_LIGHTNESS_Range_SET_UNACKNOWLEDGE   =   Opcode(0x825C, None, "Light Lightness Range Set Unacknowledged")
    

    def __init__(self):
        self.opcodes = [
            (self.LIGHT_LIGHTNESS_STATUS, self.__light_lightness_status_handler),
            (self.LIGHT_LIGHTNESS_LINEAR_STATUS, self.__light_lightness_linear_status_handler),
            (self.LIGHT_LIGHTNESS_LAST_STATUS, self.__light_lightness_last_status_handler),
            (self.LIGHT_LIGHTNESS_DEFAULT_STATUS, self.__light_lightness_default_status_handler),
            (self.LIGHT_LIGHTNESS_RANGE_STATUS, self.__light_lightness_range_status_handler)]
        self.__tid = 0
        super(LightLightnessClient, self).__init__(self.opcodes)

    def get(self):
        self.send(self.LIGHT_LIGHTNESS_GET)
        self.logger.info("Get Light Lightness")

    def set(self, lightness, transition_time_ms=0, delay_ms=0, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<HB", lightness, self._tid)
        if transition_time_ms > 0:
            message += TransitionTime.pack(transition_time_ms, delay_ms)
        if ack:
            self.send(self.LIGHT_LIGHTNESS_SET, message)
            msg = "Set Light Lightness To " + str(lightness)
            msg += ", Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.LIGHT_LIGHTNESS_SET_UNACKNOWLEDGED, message)
                msg = "Set Light Lightness To " + str(lightness)
                msg += " Unacknowledged, Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms, "
                msg += "Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def get_linear(self):
        self.send(self.LIGHT_LIGHTNESS_LINEAR_GET)
        self.logger.info("Get Light Lightness Linear")

    def set_linear(self, lightness, transition_time_ms=0, delay_ms=0, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<HB", lightness, self._tid)
        if transition_time_ms > 0:
            message += TransitionTime.pack(transition_time_ms, delay_ms)
        if ack:
            self.send(self.LIGHT_LIGHTNESS_SET, message)
            msg = "Set Light Lightness Linear To " + str(lightness)
            msg += ", Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.LIGHT_LIGHTNESS_LINEAR_SET_UNACKNOWLEDGED, message)
                msg = "Set Light Lightness Linear To " + str(lightness)
                msg += " Unacknowledged, Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms, "
                msg += "Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def get_last(self):
        self.send(self.LIGHT_LIGHTNESS_LAST_GET)
        self.logger.info("Get Light Lightness Last")

    def get_default(self):
        self.send(self.LIGHT_LIGHTNESS_DEFAULT_GET)
        self.logger.info("Get Light Lightness Default")

    def get_range(self):
        self.send(self.LIGHT_LIGHTNESS_RANGE_GET)
        self.logger.info("Get Light Lightness Range")

    def __light_lightness_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light Lightness: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 2:
            logstr += " Light Lightness Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            # present_level, = struct.unpack("<h", message.data[0:2])
            present_lightness = int(data[1], 16) << 8 | int(data[0], 16)
            # if present_level > 32767:
            #     present_level -= 65536
            logstr += " Present Lightness: " + str(present_lightness)
            if dataLength >= 4:
                # target_level, = struct.unpack("<h", message.data[2:4])
                target_lightness = int(data[3], 16) << 8 | int(data[2] ,16)
                logstr += " Target Lightness: " + str(target_lightness)
            if dataLength == 5:
                remaining_time = int(data[4], 16)
                logstr += " Remaining time: %d ms" % (TransitionTime.decode(remaining_time))
            self.logger.info(logstr)

    def __light_lightness_linear_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light Lightness Linear: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 2:
            logstr += " Light Lightness Linear Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            # present_level, = struct.unpack("<h", message.data[0:2])
            present_lightness = int(data[1], 16) << 8 | int(data[0], 16)
            # if present_level > 32767:
            #     present_level -= 65536
            logstr += " Present Lightness: " + str(present_lightness)
            if dataLength >= 4:
                # target_level, = struct.unpack("<h", message.data[2:4])
                target_lightness = int(data[3], 16) << 8 | int(data[2] ,16)
                logstr += " Target Lightness: " + str(target_lightness)
            if dataLength == 5:
                remaining_time = int(data[4], 16)
                logstr += " Remaining time: %d ms" % (TransitionTime.decode(remaining_time))
            self.logger.info(logstr)
    
    def __light_lightness_last_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light Lightness Last: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 2:
            logstr += " Light Lightness Last Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            # present_level, = struct.unpack("<h", message.data[0:2])
            last_lightness = int(data[1], 16) << 8 | int(data[0], 16)
            # if present_level > 32767:
            #     present_level -= 65536
            logstr += " Last Lightness: " + str(last_lightness)
            self.logger.info(logstr)
    
    def __light_lightness_default_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light Lightness Default: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 2:
            logstr += " Light Lightness Default Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            # present_level, = struct.unpack("<h", message.data[0:2])
            last_lightness = int(data[1], 16) << 8 | int(data[0], 16)
            # if present_level > 32767:
            #     present_level -= 65536
            logstr += " Default Lightness: " + str(last_lightness)
            self.logger.info(logstr)
    
    def __light_lightness_range_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)

        # print(''.join(['%02x' % b for b in message.data]))

        res = False
        if message is None or message.data is None:
            logstr += " Light Lightness Range: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 2:
            logstr += " Light Lightness Range Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            logstr += " Light Lightness Range "
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

    def set_default(self, lightness, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<H", lightness)
        msg = "Light Lightness Default Set" + ("" if ack else " Unacknowledged") + ":"
        msg += " lightness:" + str(lightness)
        if ack:
            self.send(self._LIGHT_LIGHTNESS_DEFAULT_SET, message)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self._LIGHT_LIGHTNESS_DEFAULT_SET_UNACKNOWLEDGE, message)
                self.logger.info(msg + " repeat:" + str(i))
                i -= 1

    def set_range(self, range_min, range_max, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<HH", range_min, range_max)
        msg = "Light Lightness Range Set" + ("" if ack else " Unacknowledged") + ":"
        msg += " range min:" + str(range_min)
        msg += " range max:" + str(range_max)
        if ack:
            self.send(self._LIGHT_LIGHTNESS_Range_SET, message)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self._LIGHT_LIGHTNESS_Range_SET_UNACKNOWLEDGE, message)
                self.logger.info(msg + " repeat:" + str(i))
                i -= 1
        
    @property
    def _tid(self):
        tid = self.__tid
        self.__tid += 1
        if self.__tid >= 255:
            self.__tid = 0
        return tid