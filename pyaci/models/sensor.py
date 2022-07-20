
from mesh.access import Model, Opcode
from models.common import TransitionTime
import struct
import re
import datetime
import time
import os

this_file_dir = os.path.dirname(os.path.abspath(__file__))

# 以下參考 android 的 DeviceProperty 數據
AVERAGE_AMBIENT_TEMPERATURE_IN_A_PERIOD_OF_DAY = 0x0001
AVERAGE_INPUT_CURRENT = 0x0002
AVERAGE_INPUT_VOLTAGE = 0x0003
AVERAGE_OUTPUT_CURRENT = 0x0004
AVERAGE_OUTPUT_VOLTAGE = 0x0005
CENTER_BEAM_INTENSITY_AT_FULL_POWER = 0x0006
CHROMATICITY_TOLERANCE = 0x0007
COLOR_RENDERING_INDEX_R9 = 0x0008
COLOR_RENDERING_INDEX_RA = 0x0009
DEVICE_APPEARANCE = 0x000A
DEVICE_COUNTRY_OF_ORIGIN = 0x000B
DEVICE_DATE_OF_MANUFACTURE = 0x000C
DEVICE_ENERGY_USE_SINCE_TURN_ON = 0x000D
DEVICE_FIRMWARE_REVISION = 0x000E
DEVICE_GLOBAL_TRADE_ITEM_NUMBER = 0x000F
DEVICE_HARDWARE_REVISION = 0x0010
DEVICE_MANUFACTURER_NAME = 0x0011
DEVICE_MODEL_NUMBER = 0x0012
DEVICE_OPERATING_TEMPERATURE_RANGE_SPECIFICATION = 0x0013
DEVICE_OPERATING_TEMPERATURE_STATISTICAL_VALUES = 0x0014
DEVICE_OVER_TEMPERATURE_EVENT_STATISTICS = 0x0015
DEVICE_POWER_RANGE_SPECIFICATION = 0x0016
DEVICE_RUN_TIME_SINCE_TURN_ON = 0x0017
DEVICE_RUNTIME_WARRANTY = 0x0018
DEVICE_SERIAL_NUMBER = 0x0019
DEVICE_SOFTWARE_REVISION = 0x001A
DEVICE_UNDER_TEMPERATURE_EVENT_STATISTICS = 0x001B
INDOOR_AMBIENT_TEMPERATURE_STATISTICAL_VALUES = 0x001C
INITIAL_CIE1931_CHROMATICITY_COORDINATES = 0x001D
INITIAL_CORRELATED_COLOR_TEMPERATURE = 0x001E
INITIAL_LUMINOUS_FLUX = 0x001F
INITIAL_PLANCKIAN_DISTANCE = 0x0020
INPUT_CURRENT_RANGE_SPECIFICATION = 0x0021
INPUT_CURRENT_STATISTICS = 0x0022
INPUT_OVER_CURRENT_EVENT_STATISTICS = 0x0023
INPUT_OVER_RIPPLE_VOLTAGE_EVENT_STATISTICS = 0x0024
INPUT_OVER_VOLTAGE_EVENT_STATISTICS = 0x0025
INPUT_UNDERCURRENT_EVENT_STATISTICS = 0x0026
INPUT_UNDER_VOLTAGE_EVENT_STATISTICS = 0x0027
INPUT_VOLTAGE_RANGE_SPECIFICATION = 0x0028
INPUT_VOLTAGE_RIPPLE_SPECIFICATION = 0x0029
INPUT_VOLTAGE_STATISTICS = 0x002A
LIGHT_CONTROL_AMBIENT_LUX_LEVEL_ON = 0x002B
LIGHT_CONTROL_AMBIENT_LUX_LEVEL_PROLONG = 0x002C
LIGHT_CONTROL_AMBIENT_LUX_LEVEL_STANDBY = 0x002D
LIGHT_CONTROL_LIGHTNESS_ON = 0x002E
LIGHT_CONTROL_LIGHTNESS_PROLONG = 0x002F
LIGHT_CONTROL_LIGHTNESS_STANDBY = 0x0030
LIGHT_CONTROL_REGULATOR_ACCURACY = 0x0031
LIGHT_CONTROL_REGULATOR_KID = 0x0032
LIGHT_CONTROL_REGULATOR_KIU = 0x0033
LIGHT_CONTROL_REGULATOR_KPD = 0x0034
LIGHT_CONTROL_REGULATOR_KPU = 0x0035
LIGHT_CONTROL_TIME_FADE = 0x0036
LIGHT_CONTROL_TIME_FADE_ON = 0x0037
LIGHT_CONTROL_TIME_FADE_STANDBY_AUTO = 0x0038
LIGHT_CONTROL_TIME_FADE_STANDBY_MANUAL = 0x0039
LIGHT_CONTROL_TIME_OCCUPANCY_DELAY = 0x003A
LIGHT_CONTROL_TIME_PROLONG = 0x003B
LIGHT_CONTROL_TIME_RUN_ON = 0x003C
LUMEN_MAINTENANCE_FACTOR = 0x003D
LUMINOUS_EFFICACY = 0x003E
LUMINOUS_ENERGY_SINCE_TURN_ON = 0x003F
LUMINOUS_EXPOSURE = 0x0040
LUMINOUS_FLUX_RANGE = 0x0041
MOTION_SENSED = 0x0042
MOTION_THRESHOLD = 0x0043
OPEN_CIRCUIT_EVENT_STATISTICS = 0x0044
OUTDOOR_STATISTICAL_VALUES = 0x0045
OUTPUT_CURRENT_RANGE = 0x0046
OUTPUT_CURRENT_STATISTICS = 0x0047
OUTPUT_RIPPLE_VOLTAGE_SPECIFICATION = 0x0048
OUTPUT_VOLTAGE_RANGE = 0x0049
OUTPUT_VOLTAGE_STATISTICS = 0x004A
OVER_OUTPUT_RIPPLE_VOLTAGE_EVENT_STATISTICS = 0x004B
PEOPLE_COUNT = 0x004C
PRESENCE_DETECTED = 0x004D
PRESENT_AMBIENT_LIGHT_LEVEL = 0x004E
PRESENT_AMBIENT_TEMPERATURE = 0x004F
PRESENT_CIE1931_CHROMATICITY_COORDINATES = 0x0050
PRESENT_CORRELATED_COLOR_TEMPERATURE = 0x0051
PRESENT_DEVICE_INPUT_POWER = 0x0052
PRESENT_DEVICE_OPERATING_EFFICIENCY = 0x0053
PRESENT_DEVICE_OPERATING_TEMPERATURE = 0x0054
PRESENT_ILLUMINANCE = 0x0055
PRESENT_INDOOR_AMBIENT_TEMPERATURE = 0x0056
PRESENT_INPUT_CURRENT = 0x0057
PRESENT_INPUT_RIPPLE_VOLTAGE = 0x0058
PRESENT_INPUT_VOLTAGE = 0x0059
PRESENT_LUMINOUS_FLUX = 0x005A
PRESENT_OUTDOOR_AMBIENT_TEMPERATURE = 0x005B
PRESENT_OUTPUT_CURRENT = 0x005C
PRESENT_OUTPUT_VOLTAGE = 0x005D
PRESENT_PLANCKIAN_DISTANCE = 0x005E
PRESENT_RELATIVE_OUTPUT_RIPPLE_VOLTAGE = 0x005F
RELATIVE_DEVICE_ENERGY_USE_IN_A_PERIOD_OF_DAY = 0x0060
RELATIVE_DEVICE_RUNTIME_IN_A_GENERIC_LEVEL_RANGE = 0x0061
RELATIVE_EXPOSURE_TIME_IN_AN_ILLUMINANCE_RANGE = 0x0062
RELATIVE_RUNTIME_IN_A_CORRELATED_COLOR_TEMPERATURE_RANGE = 0x0063
RELATIVE_RUNTIME_IN_A_DEVICE_OPERATING_TEMPERATURE_RANGE = 0x0064
RELATIVE_RUNTIME_IN_AN_INPUT_CURRENT_RANGE = 0x0065
RELATIVE_RUNTIME_IN_AN_INPUT_VOLTAGE_RANGE = 0x0066
SHORT_CIRCUIT_EVENT_STATISTICS = 0x0067
TIME_SINCE_MOTION_SENSED = 0x0068
TIME_SINCE_PRESENCE_DETECTED = 0x0069
TOTAL_DEVICE_ENERGY_USE = 0x006A
TOTAL_DEVICE_OFF_ON_CYCLES = 0x006B
TOTAL_DEVICE_POWER_ON_CYCLES = 0x006C
TOTAL_DEVICE_POWER_ON_TIME = 0x006D
TOTAL_DEVICE_RUNTIME = 0x006E
TOTAL_LIGHT_EXPOSURE_TIME = 0x006F
TOTAL_LUMINOUS_ENERGY = 0x0070
DESIRED_AMBIENT_TEMPERATURE = 0x0071
PRECISE_TOTAL_DEVICE_ENERGY_USE = 0x0072
POWER_FACTOR = 0x0073
SENSOR_GAIN = 0x0074
PRECISE_PRESENT_AMBIENT_TEMPERATURE = 0x0075
PRESENT_AMBIENT_RELATIVE_HUMIDITY = 0x0076
PRESENT_AMBIENT_CARBONDIOXIDE_CONCENTRATION = 0x0077
PRESENT_AMBIENT_VOLATILE_ORGANIC_COMPOUNDS_CONCENTRATION = 0x0078
PRESENT_AMBIENT_NOISE = 0x0079
ACTIVE_ENERGY_LOAD_SIDE = 0x0080
ACTIVE_POWER_LOAD_SIDE = 0x0081
AIR_PRESSURE = 0x0082
APPARENT_ENERGY = 0x0083
APPARENT_POWER = 0x0084
APPARENT_WIND_DIRECTION = 0x0085
APPARENT_WIND_SPEED = 0x0086
DEW_POINT = 0x0087
EXTERNAL_SUPPLY_VOLTAGE = 0x0088
EXTERNAL_SUPPLY_VOLTAGE_FREQUENCY = 0x0089
GUST_FACTOR = 0x008A
HEAT_INDEX = 0x008B
LIGHT_DISTRIBUTION = 0x008C
LIGHT_SOURCE_CURRENT = 0x008D
LIGHT_SOURCE_ON_TIME_NOT_RESETTABLE = 0x008E
LIGHT_SOURCE_ON_TIME_RESETTABLE = 0x008F
LIGHT_SOURCE_OPEN_CIRCUIT_STATISTICS = 0x0090
LIGHT_SOURCE_OVERALL_FAILURES_STATISTICS = 0x0091
LIGHT_SOURCE_SHORT_CIRCUIT_STATISTICS = 0x0092
LIGHT_SOURCE_START_COUNTER_RESETTABLE = 0x0093
LIGHT_SOURCE_TEMPERATURE = 0x0094
LIGHT_SOURCE_THERMAL_DERATING_STATISTICS = 0x0095
LIGHT_SOURCE_THERMAL_SHUTDOWN_STATISTICS = 0x0096
LIGHT_SOURCE_TOTAL_POWER_ON_CYCLES = 0x0097
LIGHT_SOURCE_VOLTAGE = 0x0098
LUMINAIRE_COLOR = 0x0099
LUMINAIRE_IDENTIFICATION_NUMBER = 0x009A
LUMINAIRE_MANUFACTURER_GTIN = 0x009B
LUMINAIRE_NOMINAL_INPUT_POWER = 0x009C
LUMINAIRE_NOMINAL_MAXIMUM_AC_MAINS_VOLTAGE = 0x009D
LUMINAIRE_NOMINAL_MINIMUM_AC_MAINS_VOLTAGE = 0x009E
LUMINAIRE_POWER_AT_MINIMUM_DIM_LEVEL = 0x009F
LUMINAIRE_TIME_OF_MANUFACTURE = 0x00A0
MAGNETIC_DECLINATION = 0x00A1
MAGNETIC_FLUX_DENSITY_2D = 0x00A2
MAGNETIC_FLUX_DENSITY_3D = 0x00A3
NOMINAL_LIGHT_OUTPUT = 0x00A4
OVERALL_FAILURE_CONDITION = 0x00A5
POLLEN_CONCENTRATION = 0x00A6
PRESENT_INDOOR_RELATIVE_HUMIDITY = 0x00A7
PRESENT_OUTDOOR_RELATIVE_HUMIDITY = 0x00A8
PRESSURE = 0x00A9
RAINFALL = 0x00AA
RATED_MEDIAN_USEFUL_LIFE_OF_LUMINAIRE = 0x00AB
RATED_MEDIAN_USEFUL_LIGHT_SOURCE_STARTS = 0x00AC
REFERENCE_TEMPERATURE = 0x00AD
TOTAL_DEVICE_STARTS = 0x00AE
TRUE_WIND_DIRECTION = 0x00AF
TRUE_WIND_SPEED = 0x00B0
UV_INDEX = 0x00B1
WIND_CHILL = 0x00B2
LIGHT_SOURCE_TYPE = 0x00B3
LUMINAIRE_IDENTIFICATION_STRING = 0x00B4
OUTPUT_POWER_LIMITATION = 0x00B5
THERMAL_DERATING = 0x00B6
OUTPUT_CURRENT_PERCENT = 0x00B7
BEACON_SENSOR_TYPE = 0x00F0
UNKNOWN = 0xFFFF
# 以上參考 android 的 DeviceProperty 數據

class SensorClient(Model):


    _SENSOR_DESCRIPTOR_GET              =   Opcode(0x8230, None, "Sensor Descriptor Get")
    _SENSOR_DESCRIPTOR_STATUS           =   Opcode(0x51, None, "Sensor Descriptor Status")
    _SENSOR_CADENCE_GET                 =   Opcode(0x8234, None, "Sensor Cadence Get")
    _SENSOR_CADENCE_SET                 =   Opcode(0x55, None, "Sensor Cadence Set")
    _SENSOR_CADENCE_SET_UNACKNOWLEDGE   =   Opcode(0x56, None, "Sensor Cadence Set Unacknowledged")
    _SENSOR_CADENCE_STATUS              =   Opcode(0x57, None, "Sensor Cadence Status")
    _SENSOR_SETTINGS_GET                =   Opcode(0x8235, None, "Sensor Settings Get")
    _SENSOR_SETTINGS_STATUS             =   Opcode(0x58, None, "Sensor Settings Status")
    _SENSOR_SETTING_GET                 =   Opcode(0x8236, None, "Sensor Setting Get")
    _SENSOR_SETTING_SET                 =   Opcode(0x59, None, "Sensor Setting Set")
    _SENSOR_SETTING_SET_UNACKNOWLEDGE   =   Opcode(0x5A, None, "Sensor Setting Set Unacknowledged")
    _SENSOR_SETTING_STATUS              =   Opcode(0x5B, None, "Sensor Setting Status")
    _SENSOR_GET                         =   Opcode(0x8231, None, "Sensor Get")
    _SENSOR_STATUS                      =   Opcode(0x52, None, "Sensor Status")
    _SENSOR_COLUMN_GET                  =   Opcode(0x8232, None, "Sensor Column Get")
    _SENSOR_COLUMN_STATUS               =   Opcode(0x53, None, "Sensor Column Status")
    _SENSOR_SERIES_GET                  =   Opcode(0x8233, None, "Sensor Series Get")
    _SENSOR_SERIES_STATUS               =   Opcode(0x54, None, "Sensor Series Status")
   
    def __init__(self):
        self.opcodes = [
            (self._SENSOR_DESCRIPTOR_STATUS     , self.__sensor_descriptor_status_handler),
            (self._SENSOR_CADENCE_STATUS     , self.__sensor_cadence_status_handler),
            (self._SENSOR_SETTINGS_STATUS    , self.__sensor_settings_status_handler),
            (self._SENSOR_SETTING_STATUS     , self.__sensor_setting_status_handler),
            (self._SENSOR_STATUS                , self.__sensor_status_handler),
            (self._SENSOR_COLUMN_STATUS         , self.__sensor_column_status_handler),
            (self._SENSOR_SERIES_STATUS         , self.__sensor_series_status_handler)]
        self.sensorPkg = ""
        self.sensorRawData = ""
        self.displayPkg = False
        self.__debug = False
        super(SensorClient, self).__init__(self.opcodes)
        self.last_cmd_resp_dict = {}

    def enableDebug(self):
        self.__debug = True
        self.sensorPkg = ""
        self.sensorRawData = ""
        self.logger.info("Sensor Debug Enabled!")


    def disableDebug(self):
        self.__debug = False
        self.sensorPkg = ""
        self.sensorRawData = ""
        self.logger.info("Sensor Debug Disabled!")


    def enablePkgDisplay(self):
        self.displayPkg = True
        self.logger.info("Display Packages Enabled!")


    def disablePkgDisplay(self):
        self.displayPkg = False
        self.logger.info("Display Packages Disabled!")


    def getSensorPkg(self):
        return self.sensorPkg


    def getSensorRawData(self):
        return self.sensorRawData


    def descriptorGet(self, propertyID=240):
        message = bytearray()
        message += struct.pack("<H", propertyID)
        self.send(self._SENSOR_DESCRIPTOR_GET, message)
        msg = "Sensor Descriptor Get"
        self.logger.info(msg)

    def cadenceGet(self, propertyID=240):
            message = bytearray()
            message += struct.pack("<H", propertyID)
            # self.logger.info(message)
            self.send(self._SENSOR_CADENCE_GET, message)
            self.logger.info("Get Cadence: propertyID:" + str(propertyID))

    def cadenceSet(self, propertyID=240, periodDivisor=1, triggerType=0, triggerDeltaDown=0, triggerDeltaUp=0, minInterval=0, low=0, high=0, ack=True, repeat=1):
        message = bytearray()
        valueLength = self.getValueLength(propertyID)
        print("valueLength:" + str(valueLength))
        # 目前先處理 1,2,4,8 的情形...
        if valueLength == 1:
            message += struct.pack("<HBBBBBB", propertyID, periodDivisor | triggerType << 7, triggerDeltaDown, triggerDeltaUp, minInterval, low, high)
        elif valueLength == 2:
            message += struct.pack("<HBHHBHH", propertyID, periodDivisor | triggerType << 7, triggerDeltaDown, triggerDeltaUp, minInterval, low, high)
        elif valueLength == 4:
            message += struct.pack("<HBLLBLL", propertyID, periodDivisor | triggerType << 7, triggerDeltaDown, triggerDeltaUp, minInterval, low, high)
        elif valueLength == 8:
            message += struct.pack("<HBQQBQQ", propertyID, periodDivisor | triggerType << 7, triggerDeltaDown, triggerDeltaUp, minInterval, low, high)

        msg = "Set Cadence" + ("" if ack else " Unacknowledged") + ":"
        msg += " propertyID:" + str(propertyID)
        msg += " periodDivisor:" + str(periodDivisor)
        msg += " triggerType:" + str(triggerType)
        msg += " triggerDeltaDown:" + str(triggerDeltaDown)
        msg += " triggerDeltaUp:" + str(triggerDeltaUp)
        msg += " minInterval:" + str(minInterval)
        msg += " fastCadenceLow:" + str(low)
        msg += " fastCadenceHigh:" + str(high)
        if ack:
            self.send(self._SENSOR_CADENCE_SET, message)
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self._SENSOR_CADENCE_SET_UNACKNOWLEDGE, message)
                self.logger.info(msg + " repeat:" + str(i))
                i -= 1

    def settingsGet(self, propertyID=240):
        message = bytearray()
        message += struct.pack("<H", propertyID)
        self.send(self._SENSOR_SETTINGS_GET, message)
        self.logger.info("Get Setting: propertyID:" + str(propertyID))

    def settingGet(self, propertyID, settingPropertyID):
        message = bytearray()
        message += struct.pack("<HH", propertyID, settingPropertyID)
        self.send(self._SENSOR_SETTING_GET, message)
        self.logger.info("Get Setting: propertyID:" + str(propertyID) + " settingPropertyID:" + str(settingPropertyID))

    def settingSet(self, propertyID, settingPropertyID, settingValue, ack=True, repeat=1):
        isValid = True
        message = bytearray()
        errMsg = ""
        if propertyID == 0x00f0:
            # IBEACON_SETTING_BEACON_ENABLE_BITMAP | IBEACON_SETTING_MAJOR_WILDCARD |
            # IBEACON_SETTING_EXISTENCE_CHECK_PERIOD
            if settingPropertyID == 0x0011 or settingPropertyID == 0x0014 \
            or settingPropertyID == 0x0018:
                message += struct.pack("<HHBH", propertyID, settingPropertyID, 2, settingValue)
            # IBEACON_SETTING_UUID |
            # IBEACON_SETTING_DFU_UUID | IBEACON_SETTING_FDT_UUID | IBEACON_SETTING_FSE_UUID
            elif settingPropertyID == 0x0012 or settingPropertyID == 0x0015 \
            or settingPropertyID == 0x0016 or settingPropertyID == 0x0017:
                settingVal = re.findall('.{2}', settingValue)
                # settingVal.reverse()
                if len(settingVal) == 16:
                    message += struct.pack("<HHB", propertyID, settingPropertyID, 16)
                    message += bytearray(int(x, 16) for x in settingVal)
                else:
                    isValid = False
                    errMsg = "Setting Value Length ERROR!"
            # IBEACON_SETTING_MAJOR_MINOR_RANGE
            elif settingPropertyID == 0x0013:
                settingVal = re.findall('.{4}', settingValue)
                # settingVal.reverse()
                if len(settingVal) == 4:
                    message += struct.pack("<HHB", propertyID, settingPropertyID, 8)
                    for x in settingVal:
                        message.append(int(x, 16) & 0xff)
                        message.append((int(x, 16) >> 8) & 0xff)
                else:
                    isValid = False
                    errMsg = "Setting Major Minor Range Value Length ERROR!"
            # IBEACON_SETTING_NONEXISTENCE_OFF_DELAY
            elif settingPropertyID == 0x0019:
                if isinstance(settingValue, int) and settingValue >= 0 and settingValue <= 255:
                    message += struct.pack("<HHBB", propertyID, settingPropertyID, 1, settingValue)
                else:
                    isValid = False
                    errMsg = "Setting Major WildCard Value Length ERROR!"
        elif propertyID == 0x004D:
            # OCCUPANCY_DIMMING_HIGH_MODE | OCCUPANCY_DIMMING_LOW_MODE | OCCUPANCY_DIMMING_TIME_DELAY
            # | OCCUPANCY_DIMMING_CUT_OFF | OCCUPANCY_DIMMING_SENSITIVITY | OCCUPANCY_DIMMING_HOLD_OFF_SETPOINT
            if settingPropertyID in [1,2,3,4,5,6]:
                if isinstance(settingValue, int) and settingValue >= 0 and settingValue <= 65535:
                    message += struct.pack("<HHBH", propertyID, settingPropertyID, 2, settingValue)
                else:
                    isValid = False
                    errMsg = "MDH Setting Value Length ERROR!"
            # OCCUPANCY_DIMMING_FORCE_OFF_SETPOINT_WITH_OCCUPIED | OCCUPANCY_DIMMING_RAMP_UP
            # | OCCUPANCY_DIMMING_FADE_DOWN |OCCUPANCY_DIMMING_WALK_THROUGH_MODE
            # | OCCUPANCY_DIMMING_OCCUPANCY_MODE
            elif settingPropertyID in [7,8,9,10,11]:
                if isinstance(settingValue, int) and settingValue >= 0 and settingValue <= 255:
                    if settingPropertyID in [7,10,11] and settingValue not in [0,1]:
                        isValid = False
                        errMsg = "MDH Setting Value ERROR!"
                    else:
                        message += struct.pack("<HHBB", propertyID, settingPropertyID, 1, settingValue)
                else:
                    isValid = False
                    errMsg = "MDH Setting Value Length ERROR!"
            else:
                isValid = False
        else:
            isValid = False

        if isValid:
            msg = "Set " + ("Beacon" if propertyID == 0x00f0 else "MDH") + " Setting" + ("" if ack else " Unacknowledged") + ":"
            msg += " propertyID:" + str(propertyID)
            msg += " settingPropertyID:" + str(settingPropertyID)
            msg += " settingValue:" + str(settingValue)
            if ack:
                self.send(self._SENSOR_SETTING_SET, message)
                self.logger.info(msg)
            else:
                i = repeat
                while i > 0:
                    time.sleep(0.5)
                    self.send(self._SENSOR_SETTING_SET_UNACKNOWLEDGE, message)
                    self.logger.info(msg + " repeat:" + str(i))
                    i -= 1
        else:
            self.logger.info("setting set/get message ERROR:" + errMsg)


    def get(self, propertyID=240):
        message = bytearray()
        message += struct.pack("<H", propertyID)
        self.send(self._SENSOR_GET, message)
        msg = "Sensor Get"
        self.logger.info(msg)


    def columnGet(self, propertyID, rawValueX):
        message = bytearray()
        message += struct.pack("<H", propertyID)
        valLen = int(rawValueX / 255) + 1
        i = 0
        while i < valLen:
            message.append(rawValueX >> (i*8) & 0xFF)
            i += 1
        self.send(self._SENSOR_COLUMN_GET, message)
        msg = "Sensor Column Get"
        self.logger.info(msg)


    def seriesGet(self, propertyID, rawValueX1, rawValueX2):
        message = bytearray()
        message += struct.pack("<H", propertyID)
        valLen = int(rawValueX1 / 255) + 1
        i = 0
        while i < valLen:
            message.append(rawValueX1 >> (i*8) & 0xFF)
            i += 1
        valLen = int(rawValueX2 / 255) + 1
        i = 0
        while i < valLen:
            message.append(rawValueX2 >> (i*8) & 0xFF)
            i += 1
        self.send(self._SENSOR_SERIES_GET, message)
        msg = "Sensor Series Get"
        self.logger.info(msg)


    # @property
    def __sensor_descriptor_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        # print("dataLen:"+str(dataLen))
        result = []

        if dataLen == 2:
            resp = bytearray([data[1], data[0]])
        elif dataLen % 8 == 0:
            resp = bytearray()
            count = int(dataLen / 8)
            i = 0
            while i < count:
                PropertyID =  data[i * 8] + data[i * 8 + 2] * 256
                # print("PropertyID:"+str(PropertyID))
                result.append( PropertyID )
                resp += bytearray([data[i * 8 + 1], data[i * 8], data[i * 8 + 2], data[i * 8 + 3], data[i * 8 + 4], data[i * 8 + 5], data[i * 8 + 6], data[i * 8 + 7]])
                i += 1
        else:
            resp = data

        self.last_cmd_resp_dict[0] = result
        # print("result:"+str(result))

        if message is None or message.data is None:
            logstr += " Sensor Descriptor Status: message is None!!"
        elif len(message.data) < 2:
            logstr += " Sensor Descriptor Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
        elif len(message.data) == 2:
            propertyID, = struct.unpack("<h", message.data[0:2])
            logstr += " Property ID: " + str(propertyID)
        else:
            logstr += " Sensor Descriptor Status: " + ''.join('%02x' % b for b in message.data)
        self.logger.info(logstr)

    # @property

    def __sensor_cadence_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        ttl = message.meta['ttl']
        logstr = "unicastAddress:" + str(dongleUnicastAddress) \
            + ",ttl:" + str(ttl)


        if message is None or message.data is None:
            logstr += ",Sensor Cadence Status: message is None!!"
            resp = message.data
        elif len(message.data) < 8:
            logstr += ",Sensor Cadence Status Error: msg="
            logstr += ''.join(['%02x' % b for b in message.data])
            resp = message.data
        else:
            data = message.data
            valueLength = self.getValueLength(data[0] + data[1] * 256)
            print("valueLength:"+str(valueLength))

            propertyID = data[0] + data[1] * 256
            periodDivisor = data[2] & 0x07
            triggerType = data[2] >> 7 & 0x01
            minInterval = data[3+2*valueLength]
            triggerDeltaDown = 0
            triggerDeltaUp = 0
            fastCadenceLow = 0
            fastCadenceHigh = 0
            for i in range(valueLength):
                triggerDeltaDown *= 256
                triggerDeltaUp *= 256
                fastCadenceLow *= 256
                fastCadenceHigh *= 256
                triggerDeltaDown += data[2+(valueLength-i)]
                triggerDeltaUp += data[2+valueLength+(valueLength-i)]
                fastCadenceLow += data[3+2*valueLength+(valueLength-i)]
                fastCadenceHigh += data[3+3*valueLength+(valueLength-i)]

            logstr += "Sensor Cadence New Status:"
            logstr += "propertyID:" + str(propertyID)
            logstr += " periodDivisor:" + str(periodDivisor)
            logstr += " triggerType:" + str(triggerType)
            logstr += " triggerDeltaDown:" + str(triggerDeltaDown)
            logstr += " triggerDeltaUp:" + str(triggerDeltaUp)
            logstr += " minInterval:" + str(minInterval)
            logstr += " fastCadenceLow:" + str(fastCadenceLow)
            logstr += " fastCadenceHigh:" + str(fastCadenceHigh)

            # if valueLength == 1:
            #     logstr += ",Sensor Cadence Status:"
            #     logstr += "propertyID:" + str(data[0] + data[1] * 256)
            #     logstr += " periodDivisor:" + str(data[2] & 0x07)
            #     logstr += " triggerType:" + str(data[2] >> 7 & 0x01)
            #     logstr += " triggerDeltaDown:" + str(data[3] )
            #     logstr += " triggerDeltaUp:" + str(data[4] )
            #     logstr += " minInterval:" + str(data[5])
            #     logstr += " fastCadenceLow:" + str(data[6] )
            #     logstr += " fastCadenceHigh:" + str(data[7] )
            # elif valueLength == 2:
            #     logstr += ",Sensor Cadence Status:"
            #     logstr += "propertyID:" + str(data[0] + data[1] * 256)
            #     logstr += " periodDivisor:" + str(data[2] & 0x07)
            #     logstr += " triggerType:" + str(data[2] >> 7 & 0x01)
            #     logstr += " triggerDeltaDown:" + str(data[3] + data[4] * 256)
            #     logstr += " triggerDeltaUp:" + str(data[5] + data[6] * 256)
            #     logstr += " minInterval:" + str(data[7])
            #     logstr += " fastCadenceLow:" + str(data[8] + data[9] * 256)
            #     logstr += " fastCadenceHigh:" + str(data[10] + data[11] * 256)

            self.last_cmd_resp_dict[propertyID] = [
                propertyID ,
                periodDivisor ,
                triggerType ,
                triggerDeltaDown ,
                triggerDeltaUp ,
                minInterval ,
                fastCadenceLow,
                fastCadenceHigh
            ]

            # resp = bytearray([data[1], data[0], data[2] & 0x07, data[2] >> 7 & 0x01,
            #     data[4], data[3], data[6], data[5], data[7], data[9], data[8], data[11], data[10]])
            resp = message.data

        self.logger.info(logstr)

    def __sensor_settings_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        ttl = message.meta['ttl']
        logstr = "unicastAddress:" + str(dongleUnicastAddress) \
            + ",ttl:" + str(ttl)
        if message is None or message.data is None:
            logstr += ",Sensor Settings Status: message is None!!"
            resp = message.data
        elif len(message.data) < 2:
            logstr += ",Sensor Settings Status Error: msg="
            logstr += ''.join(['%02x' % b for b in message.data])
            resp = message.data
        else:
            resp = bytearray()
            data = message.data

            propertyID = data[0] + data[1] * 256



            logstr += ",Sensor Settings Status:"
            logstr += "propertyID:" + str( propertyID )
            resp += bytearray([data[1], data[0]])
            settings = data[2:]
            settingCount = int(len(settings) / 2)
            logstr += " settingsCount:" + str(settingCount)
            result = []
            if settingCount > 0:
                logstr += " settingPropertyIDList:"
                i = 0
                while i < settingCount:
                    settingPropertyID = settings[2*i] + settings[2*i+1] * 256
                    resp += bytearray([settings[2*i+1], settings[2*i]])
                    logstr += str(settingPropertyID) + " "
                    result.append(settingPropertyID)
                    i += 1
            self.last_cmd_resp_dict[propertyID] = result

        self.logger.info(logstr)

    def __sensor_setting_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        ttl = message.meta['ttl']
        logstr = "unicastAddress:" + str(dongleUnicastAddress) \
            + ",ttl:" + str(ttl)
        if message is None or message.data is None:
            logstr += ",Sensor Setting Status: message is None!!"
            resp = message.data
        elif len(message.data) < 6:
            logstr += ",Sensor Setting Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            resp = message.data
        else:
            data = message.data
            propertyID = data[0] + data[1] * 256
            logstr += ",Sensor " + ("Beacon" if propertyID == 240 else "MDH") + " Setting Status:"
            settingPropertyID = data[2] + data[3] * 256
            tmp_key = str(propertyID)+"."+str(settingPropertyID)
            # print("__sensor_setting_status_handler:tmp_key:"+tmp_key)
            self.last_cmd_resp_dict[tmp_key] = ['%02x' % b for b in  data[4:] ]

            logstr += "propertyID:" + str(propertyID)
            logstr += " settingPropertyID:" + str(settingPropertyID)
            logstr += " settingAccess:" + str(data[4])
            dataLen = len(data)
            resp = bytearray([data[1], data[0], data[3], data[2], data[4], data[5]])
            if propertyID == 240:
                if settingPropertyID not in [0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19] or dataLen != data[5] + 6:
                    logstr = "Sensor Beacon Setting Status Error: msg=" 
                    logstr += ''.join(['%02x' % b for b in message.data])
                    resp = message.data
                elif (settingPropertyID == 0x19 and data[5] != 1) or \
                (settingPropertyID in [0x11,0x14,0x18] and data[5] != 2) or \
                (settingPropertyID == 0x13 and data[5] != 8) or \
                (settingPropertyID in [0x12,0x15,0x16,0x17] and data[5] != 16):
                    logstr = "Sensor Beacon Setting Status Error: msg=" 
                    logstr += ''.join(['%02x' % b for b in message.data])
                    resp = message.data
                else:
                    if settingPropertyID == 0x11:
                        resp += bytearray([data[7], data[6]])
                        logstr += " beaconEnable:"
                        if data[6] & 0x3F == 0x00:
                            logstr += "None "
                        else:
                            if data[6] & 0x01 == 0x01:
                                logstr += "iBeacon "
                            if data[6] & 0x02 == 0x02:
                                logstr += "EddystoneTLM "
                            if data[6] & 0x04 == 0x04:
                                logstr += "DeviceInfo "
                            if data[6] & 0x08 == 0x08:
                                logstr += "SmartWatchBeacon "
                            if data[6] & 0x10 == 0x10:
                                logstr += "iBeaconDistance "
                            if data[6] & 0x20 == 0x20:
                                logstr += "ImprovediBeaconDistance "
                    elif settingPropertyID == 0x12:
                        logstr += " settingUUID:"
                        logstr += ''.join(['%02x' % b for b in data[6:]])
                        resp += bytearray(data[6:])
                    elif settingPropertyID == 0x13:
                        logstr += " majorLL:" + str(data[6] + data[7] * 256)
                        logstr += " majorUL:" + str(data[8] + data[9] * 256)
                        logstr += " minorLL:" + str(data[10] + data[11] * 256)
                        logstr += " minorUL:" + str(data[12] + data[13] * 256)
                        resp += bytearray([data[7], data[6], data[9], data[8], data[11], data[10], data[13], data[12]])
                        # logstr += " majorLL:" + str(data[7] + data[6] * 256)
                        # logstr += " majorUL:" + str(data[9] + data[8] * 256)
                        # logstr += " minorLL:" + str(data[11] + data[10] * 256)
                        # logstr += " minorUL:" + str(data[13] + data[12] * 256)
                        # resp += bytearray([data[7], data[6], data[9], data[8], data[11], data[10], data[13], data[12]])
                    elif settingPropertyID == 0x14:
                        logstr += " majorWildCard:" + str(data[6] + data[7] * 256)
                        resp += bytearray([data[7], data[6]])
                    elif settingPropertyID == 0x15:
                        logstr += " DFU_UUID:"
                        logstr += ''.join(['%02x' % b for b in data[6:]])
                        resp += bytearray(data[6:])
                    elif settingPropertyID == 0x16:
                        logstr += " FDT_UUID:"
                        logstr += ''.join(['%02x' % b for b in data[6:]])
                        resp += bytearray(data[6:])
                    elif settingPropertyID == 0x17:
                        logstr += " FSE_UUID:"
                        logstr += ''.join(['%02x' % b for b in data[6:]])
                        resp += bytearray(data[6:])
                    elif settingPropertyID == 0x18:
                        logstr += " existenceCheckPeriod:" + str(data[6] + data[7] * 256) + "ms"
                        resp += bytearray([data[7], data[6]])
                    elif settingPropertyID == 0x19:
                        logstr += " nonexistenceLightOffDelay:" + str(data[6]) + "s"
                        resp.append(data[6])
            elif propertyID == 77:
                if settingPropertyID in [1,2,3,4,5,6] and data[5] == 2 and dataLen == 8:
                    valStr = str(data[6] + data[7] * 256)
                    if settingPropertyID == 1:
                        logstr += " occupiedDimmingHighModeLevel:"
                    elif settingPropertyID == 2:
                        logstr += " occupiedDimmingLowModeLevel:"
                    elif settingPropertyID == 3:
                        logstr += " occupiedDimmingTimeDelay:"
                    elif settingPropertyID == 4:
                        logstr += " occupiedDimmingCutOffWaitingTime:"
                    elif settingPropertyID == 5:
                        logstr += " occupiedDimmingSensitivity:"
                    elif settingPropertyID == 6:
                        logstr += " occupiedDimmingHoldOffSetpoint:"
                    logstr += valStr
                    resp += bytearray([data[7], data[6]])
                elif settingPropertyID in [7,8,9,10,11] and data[5] == 1 and dataLen == 7:
                    valDisableStr = ["Disabled", "Enabled"]
                    if settingPropertyID == 7 and data[6] in [0,1]:
                        logstr += " occupiedDimmingForceOffSetpointWithOccupied:" + valDisableStr[data[6]]
                    elif settingPropertyID == 8:
                        logstr += " occupiedDimmingRampUp:" + str(data[6])
                    elif settingPropertyID == 9:
                        logstr += " occupiedDimmingFadeDown:" + str(data[6])
                    elif settingPropertyID == 10:
                        logstr += " occupiedDimmingWalkThroughMode:" + valDisableStr[data[6]]
                    elif settingPropertyID == 11:
                        logstr += " occupiedDimmingOccupanyMode:" + valDisableStr[data[6]]
                    resp += bytearray([data[6]])
                else:
                    logstr = "Sensor MDH Setting Status Error: msg=" 
                    logstr += ''.join(['%02x' % b for b in message.data])
                    resp = message.data
        self.logger.info(logstr)

    def __sensor_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        ttl = message.meta['ttl']
        if self.__debug:
            self.sensorRawData += str(time.time()) + "-" + '%04x' % dongleUnicastAddress + nodeUUID + '%02x' % ttl \
                + ''.join('%02x' % x for x in message.data) + "\n"
        data = ['%02x' % b for b in message.data]
        if message is None or message.data is None or len(message.data) <= 0:
            logstr = "Sensor Status: message or data is None!!"
            self.logger.info(logstr)
        elif len(data) < 10:
            logstr = "Sensor Status Error: msg=" 
            logstr += ''.join('%02x' % b for b in message.data)
            self.logger.info(logstr)
        elif len(data) >= 10:
            # 101e 07 01000a0011c5c3    101e 07 01001e0022c5bc
            while len(data) >= 10:
                msg = ""
                # iBeacon
                if int(data[2], 16) == 7 and int(data[3], 16) == 1:
                    majorID = int(data[4], 16) << 8 | int(data[5], 16)
                    minorID = int(data[6], 16) << 8 | int(data[7], 16)
                    signalPower = int(data[8], 16)
                    rssi = int(data[9], 16) - 256
                    msg = "unicastAddress:" + str(dongleUnicastAddress) \
                            + ",ttl:" + str(ttl) \
                            + ",iBeacon, majorID:" + str(majorID) \
                            + ",minorID:" + str(minorID) + ",signalPower:" \
                            + str(signalPower) + ",Rssi:" + str(rssi)
                    data = data[10:]
                # DeviceInfo
                elif int(data[2], 16) == 8 and int(data[3], 16) == 3:
                    macAddress = str(data[4]) + ":" + str(data[5]) + ":" + str(data[6]) \
                    + ":" + str(data[7]) + ":" + str(data[8]) + ":" + str(data[9])
                    batteryLevel = int(data[10], 16)
                    msg = "unicastAddress:" + str(dongleUnicastAddress) \
                            + ",ttl:" + str(ttl) \
                            + ",DeviceInfo, macAddress:" + macAddress \
                            + ",batteryLevel:" + str(batteryLevel) + "%"
                    data = data[11:]
                # EddyStone
                elif int(data[2], 16) == 12 and int(data[3], 16) == 2 \
                    and int(data[4], 16) == 0x20:
                    macAddress = str(data[6]) + ":" + str(data[7]) + ":" \
                    + str(data[8]) + ":" + str(data[9]) + ":" + str(data[10]) \
                    + ":" + str(data[11])
                    voltage = '%.2f' % ((int(data[11], 16) << 8 | int(data[12], 16)) * 0.001)
                    temp = int(data[13], 16) + (int(data[14], 16) / 255.0)
                    msg = "unicastAddress:" + str(dongleUnicastAddress) \
                            + ",ttl:" + str(ttl) \
                            + ",EddyStone, macAddress:" + macAddress \
                            + ",voltage:" + str(voltage) + "V, temp:" + str(temp) + "℃"
                    data = data[15:]
                # SmartWatchBeacon
                elif int(data[2], 16) == 17 and int(data[3], 16) == 4:
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
                    data = data[20:]
                # iBeaconDistance
                elif int(data[2], 16) == 7 and int(data[3], 16) == 5:
                    majorID = int(data[4], 16) << 8 | int(data[5], 16)
                    minorID = int(data[6], 16) << 8 | int(data[7], 16)
                    dist = int(data[8], 16)
                    rssi = int(data[9], 16) - 256
                    distance = "immediate" if dist == 0 else ("near" if dist == 1 else ("far" if dist == 2 else "unknown")) 
                    msg = "unicastAddress:" + str(dongleUnicastAddress) \
                            + ",ttl:" + str(ttl) \
                            + ",iBeaconDistance, majorID:" + str(majorID) \
                            + ",minorID:" + str(minorID) + ",Rssi:" + str(rssi) \
                            + ",Distance:" + distance
                    data = data[10:]
                # ImprovediBeaconDistance
                elif int(data[2], 16) == 7 and int(data[3], 16) == 6:
                    majorID = int(data[4], 16) << 8 | int(data[5], 16)
                    minorID = int(data[6], 16) << 8 | int(data[7], 16)
                    dist = int(data[8], 16)
                    rssi = int(data[9], 16) - 256
                    distance = "immediate" if dist == 0 else ("near" if dist == 1 else ("far" if dist == 2 else "unknown")) 
                    msg = "unicastAddress:" + str(dongleUnicastAddress) \
                            + ",ttl:" + str(ttl) \
                            + ",ImprovediBeaconDistance, majorID:" + str(majorID) \
                            + ",minorID:" + str(minorID) + ",Rssi:" + str(rssi) \
                            + ",ImprovedDistance:" + distance
                    data = data[10:]
                else:
                    self.logger.info(''.join('%02x' % b for b in message.data))
                if msg != '':
                    if self.displayPkg:
                        self.logger.info(msg)
                    if self.__debug:
                        self.sensorPkg += str(time.time()) + "-" + msg + "\n"
        if self.__debug:
            if len(self.sensorPkg) > 102400:
                fp = open(this_file_dir+"/data/sensor_pkg_" + str(time.time()) + ".txt", "w+")
                fp.write(self.sensorPkg)
                fp.close()
                self.sensorPkg = ""
            if len(self.sensorRawData) > 102400:
                fp = open(this_file_dir+"/data/sensor_raw_data_" + str(time.time()) + ".txt", "w+")
                fp.write(self.sensorRawData)
                fp.close()
                self.sensorRawData = ""


    def __sensor_column_status_handler(self, opcode, message):
        self.logger.info("Sensor Column Status:" + ''.join('%02x' % b for b in message.data))
        
    def __sensor_series_status_handler(self, opcode, message):
        self.logger.info("Sensor Series Status:" + ''.join('%02x' % b for b in message.data))

    def getValueLength(self,propertyID):
        # 以下參考 android 的 DeviceProperty 數據
        lengths = {
            PRECISE_PRESENT_AMBIENT_TEMPERATURE: 2,
            PRESENT_DEVICE_OPERATING_TEMPERATURE: 2,
            PEOPLE_COUNT: 2,
            PRESENT_AMBIENT_RELATIVE_HUMIDITY: 2,
            PRESENT_INDOOR_RELATIVE_HUMIDITY: 2,
            PRESENT_OUTDOOR_RELATIVE_HUMIDITY: 2,
            LIGHT_CONTROL_LIGHTNESS_ON: 2,
            LIGHT_CONTROL_LIGHTNESS_PROLONG: 2,
            LIGHT_CONTROL_LIGHTNESS_STANDBY: 2,
            TIME_SINCE_MOTION_SENSED: 2,
            TIME_SINCE_PRESENCE_DETECTED: 2,
            LIGHT_SOURCE_START_COUNTER_RESETTABLE: 3,
            LIGHT_SOURCE_TOTAL_POWER_ON_CYCLES: 3,
            RATED_MEDIAN_USEFUL_LIGHT_SOURCE_STARTS: 3,
            TOTAL_DEVICE_OFF_ON_CYCLES: 3,
            TOTAL_DEVICE_POWER_ON_CYCLES: 3,
            TOTAL_DEVICE_STARTS: 3,
            LIGHT_CONTROL_AMBIENT_LUX_LEVEL_ON: 3,
            LIGHT_CONTROL_AMBIENT_LUX_LEVEL_PROLONG: 3,
            LIGHT_CONTROL_AMBIENT_LUX_LEVEL_STANDBY: 3,
            PRESENT_AMBIENT_LIGHT_LEVEL: 3,
            PRESENT_ILLUMINANCE: 3,
            DEVICE_RUN_TIME_SINCE_TURN_ON: 3,
            DEVICE_RUNTIME_WARRANTY: 3,
            RATED_MEDIAN_USEFUL_LIFE_OF_LUMINAIRE: 3,
            TOTAL_DEVICE_POWER_ON_TIME: 3,
            TOTAL_DEVICE_RUNTIME: 3,
            TOTAL_LIGHT_EXPOSURE_TIME: 3,
            LIGHT_CONTROL_TIME_FADE: 3,
            LIGHT_CONTROL_TIME_FADE_ON: 3,
            LIGHT_CONTROL_TIME_FADE_STANDBY_AUTO: 3,
            LIGHT_CONTROL_TIME_FADE_STANDBY_MANUAL: 3,
            LIGHT_CONTROL_TIME_OCCUPANCY_DELAY: 3,
            LIGHT_CONTROL_TIME_PROLONG: 3,
            LIGHT_CONTROL_TIME_RUN_ON: 3,
            DEVICE_DATE_OF_MANUFACTURE: 3,
            LUMINAIRE_TIME_OF_MANUFACTURE: 3,
            PRESSURE: 4,
            AIR_PRESSURE: 4,
            LIGHT_CONTROL_REGULATOR_KID: 4,
            LIGHT_CONTROL_REGULATOR_KIU: 4,
            LIGHT_CONTROL_REGULATOR_KPD: 4,
            LIGHT_CONTROL_REGULATOR_KPU: 4,
            SENSOR_GAIN: 4,
            BEACON_SENSOR_TYPE: 2,
            DEVICE_FIRMWARE_REVISION: 8,
            DEVICE_SOFTWARE_REVISION: 8,
            DEVICE_HARDWARE_REVISION: 16,
            DEVICE_SERIAL_NUMBER: 16,
            DEVICE_MODEL_NUMBER: 24,
            LUMINAIRE_COLOR: 24,
            LUMINAIRE_IDENTIFICATION_NUMBER: 24,
            DEVICE_MANUFACTURER_NAME: 36,
            LUMINAIRE_IDENTIFICATION_STRING: 64,
            PRESENCE_DETECTED: 1,
            LIGHT_CONTROL_REGULATOR_ACCURACY: 1,
            OUTPUT_RIPPLE_VOLTAGE_SPECIFICATION: 1,
            INPUT_VOLTAGE_RIPPLE_SPECIFICATION: 1,
            OUTPUT_CURRENT_PERCENT: 1,
            LUMEN_MAINTENANCE_FACTOR: 1,
            MOTION_SENSED: 1,
            MOTION_THRESHOLD: 1,
            PRESENT_DEVICE_OPERATING_EFFICIENCY: 1,
            PRESENT_RELATIVE_OUTPUT_RIPPLE_VOLTAGE: 1,
            PRESENT_INPUT_RIPPLE_VOLTAGE: 1,
            DESIRED_AMBIENT_TEMPERATURE: 1,
            PRESENT_AMBIENT_TEMPERATURE: 1,
            PRESENT_INDOOR_AMBIENT_TEMPERATURE: 1,
            PRESENT_OUTDOOR_AMBIENT_TEMPERATURE: 1
        }
        return lengths.get(propertyID,None)