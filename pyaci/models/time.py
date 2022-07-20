from mesh.access import Model, Opcode
from models.common import TransitionTime
import struct
import datetime
import time


class TimeClient(Model):
    _TIME_GET                      =   Opcode(0x8237, None, "Time Get")
    _TIME_STATUS                   =   Opcode(0x5D, None, "Time Status")
    _TIME_ZONE_GET                 =   Opcode(0x823B, None, "Time Zone Get")
    _TIME_ZONE_STATUS              =   Opcode(0x823D, None, "Time Zone Status")
    _TAI_UTC_DELTA_GET             =   Opcode(0x823E, None, "TAI-UTC Delta Get")
    _TAI_UTC_DELTA_STATUS          =   Opcode(0x8240, None, "TAI-UTC Delta Status")
    _TIME_SET                      =   Opcode(0x5C, None, "Time Set")
    _TIME_ZONE_SET                 =   Opcode(0x823C, None, "Time Zone Set")
    _TAI_UTC_DELTA_SET             =   Opcode(0x823F, None, "TAI-UTC Delta Set")
    _TIME_ROLE_GET                 =   Opcode(0x8238, None, "Time Role Get")
    _TIME_ROLE_SET                 =   Opcode(0x8239, None, "Time Role Set")
    _TIME_ROLE_STATUS              =   Opcode(0x823A, None, "Time Role Status")

    def __init__(self):
        self.opcodes = [
            (self._TIME_STATUS                 , self.__time_status_handler),
            (self._TIME_ZONE_STATUS            , self.__time_zone_status_handler),
            (self._TAI_UTC_DELTA_STATUS        , self.__tai_utc_delta_status_handler),
            (self._TIME_ROLE_STATUS                 , self.__time_role_status_handler)]

        self.__baseTai = datetime.datetime(2000, 1, 1, 0, 0, 0)
        super(TimeClient, self).__init__(self.opcodes)

    def timeGet(self):
        self.send(self._TIME_GET)
        self.logger.info("Get Time")

    def timeZoneGet(self):
        self.send(self._TIME_ZONE_GET)
    
    def taiUtcDeltaGet(self):
        self.send(self._TAI_UTC_DELTA_GET)

    def utcToTai(self, utcTime, offset=37):
        # now = datetime.datetime(year, month, day, hour, minute, second)
        # return int((utcTime - self.__baseTai).total_seconds()) + offset
        return int((utcTime - self.__baseTai).total_seconds())

    def taiToUtc(self, tai, offset=37):
        # now = tai + time.mktime(self.__baseTai.timetuple()) - offset
        now = tai + time.mktime(self.__baseTai.timetuple())
        return datetime.datetime.utcfromtimestamp(now) + datetime.timedelta(hours=8)

    def __time_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        if message is None or message.data is None:
            logstr += " Time Status: message is None!!"
        elif len(message.data) < 10:
            logstr += " Time Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
        else:
            logstr += " Time Status: "
            tai = int(message.data[0]) | int(message.data[1]) << 8 | int(message.data[2]) << 16 \
                | int(message.data[3]) << 24 | int(message.data[4]) << 32
            utcTime = self.taiToUtc(tai)
            y = utcTime.year - 2000
            m = utcTime.month
            d = utcTime.day
            h = utcTime.hour
            i = utcTime.minute
            s = utcTime.second
            logstr += str(utcTime.year) + "/" + ('%02d' % m) + "/" + ('%02d' % d) + " " 
            logstr += ('%02d' % h) + ":" + ('%02d' % i) + ":" + ('%02d' % s) 
            # self.logger.info(utcTime)
            resp = bytearray([y, m, d, h, i, s])
        self.logger.info(logstr)


    def timeRoleGet(self):
        self.send(self._TIME_ROLE_GET)

    def utcToTai(self, utcTime, offset=37):
        # now = datetime.datetime(year, month, day, hour, minute, second)
        # return int((utcTime - self.__baseTai).total_seconds()) + offset
        return int((utcTime - self.__baseTai).total_seconds())

    def taiToUtc(self, tai, offset=37):
        # now = tai + time.mktime(self.__baseTai.timetuple()) - offset
        now = tai + time.mktime(self.__baseTai.timetuple())
        return datetime.datetime.utcfromtimestamp(now) + datetime.timedelta(hours=8)

    def timeSet(self, year=0, month=0, day=0, hour=0, minute=0, second=0, subSecond=0, uncertainty=0, auth=0, tuDelta=0, timeZoneOffset=0):
        message = bytearray()
        if year == 0 and month == 0 and day == 0 :
            utcTime = datetime.datetime.now()
        else:
            utcTime = datetime.datetime(year + 2000, month, day, hour, minute, second)
        tai = self.utcToTai(utcTime)
        message += struct.pack("<BBBBBBBHB", tai & 0xff, tai >> 8 & 0xff, \
            tai >> 16 & 0xff, tai >> 24 & 0xff, tai >> 32 & 0xff,\
            subSecond, uncertainty, (auth << 15) | tuDelta, timeZoneOffset)
        self.send(self._TIME_SET, message)
        msg = "Set Time To: %4d/%02d/%02d %02d:%02d:%02d, " % (utcTime.year, utcTime.month, utcTime.day, utcTime.hour, utcTime.minute, utcTime.second)
        msg += "subSecond:%d, uncertainty:%d, auth:%d, tuDelta:%d, timeZoneOffset:%d" % (subSecond, uncertainty, auth, tuDelta, timeZoneOffset)
        self.logger.info(msg)

    def timeZoneSet(self, timeZoneOffset, taiOfZone):
        message = bytearray()
        message += struct.pack("<BBBBBB", timeZoneOffset, taiOfZone & 0xff, taiOfZone >> 8 & 0xff, \
            taiOfZone >> 16 & 0xff, taiOfZone >> 24 & 0xff, taiOfZone >> 32 & 0xff)
        self.logger.info(message)
        self.send(self._TIME_ZONE_SET, message)

    def taiUtcDeltaSet(self, taiUtcDelta, taiOfZone):
        message = bytearray()
        message += struct.pack("<HBBBBB", taiUtcDelta << 1, taiOfZone & 0xff, taiOfZone >> 8 & 0xff, \
            taiOfZone >> 16 & 0xff, taiOfZone >> 24 & 0xff, taiOfZone >> 32 & 0xff)
        self.logger.info(message)
        self.send(self._TAI_UTC_DELTA_SET, message)

    def timeRoleSet(self, timeRole):
        message = bytearray()
        message += struct.pack("<B", timeRole)
        self.logger.info(message)
        self.send(self._TIME_ROLE_SET, message)
        
    def __time_zone_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        if message is None or message.data is None:
            logstr += " Time Zone Status: message is None!!"
            return
        if len(message.data) < 7:
            logstr += " Time Zone Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            return
        logstr += " Time Zone Status: "
        logstr += ''.join(['%02x' % b for b in message.data])
        self.logger.info(logstr)

    def __tai_utc_delta_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        if message is None or message.data is None:
            logstr += " TAI-UTC Delta Status: message is None!!"
            return
        if len(message.data) < 9:
            logstr += " TAI-UTC Delta Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            return
        logstr += " TAI-UTC Delta: "
        logstr += ''.join(['%02x' % b for b in message.data])
        self.logger.info(logstr)

    def __time_role_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        if message is None or message.data is None:
            logstr += " Time Role Status: message is None!!"
            return
        if len(message.data) < 1:
            logstr += " Time Role Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            return
        timeRole, = struct.unpack("<B", message.data[0])
        logstr += " Time Role: " + str(timeRole)
        self.logger.info(logstr)