from mesh.access import Model, Opcode
from models.common import TransitionTime
import struct
from datetime import datetime
import time


class SchedulerClient(Model):
    _SCHEDULER_ACTION_GET               =   Opcode(0x8248, None, "Scheduler Action Get")
    _SCHEDULER_ACTION_STATUS            =   Opcode(0x5F,   None, "Scheduler Action Status")
    _SCHEDULER_GET                      =   Opcode(0x8249, None, "Scheduler Get")
    _SCHEDULER_STATUS                   =   Opcode(0x824A, None, "Scheduler Status")
    _SCHEDULER_ACTION_SET                        =   Opcode(0x60, None, "Scheduler Action Set")
    _SCHEDULER_ACTION_SET_UNACKNOWLEDGED         =   Opcode(0x61, None, "Scheduler Action Set Unacknowledged")
    
    def __init__(self):
        self.opcodes = [
            (self._SCHEDULER_ACTION_STATUS      , self.__scheduler_action_status_handler),
            (self._SCHEDULER_STATUS             , self.__scheduler_status_handler)]
        self.__tid = 0
        self.__scheduler_month = ["January ","February ","March ","April ",\
        "May ","June ","July ","August ","September ","October ","November ","December "]
        self.__scheduler_week = ["Monday ","Tuesday ","Wednesday ","Thursday ",\
        "Friday ","Saturday ","Sunday "]
        self.__scheduler_actions = {"0":"Turn Off", "1":"Turn On", "2":"Scene Recall", "15":"No Action"}
        self.last_cmd_resp_dict = {}
        super(SchedulerClient, self).__init__(self.opcodes)

    def schedulerActionGet(self, schedulerIndex):
        message = bytearray()
        message += struct.pack("<B", schedulerIndex)
        self.send(self._SCHEDULER_ACTION_GET, message)
        msg = "Get Scheduler " + str(schedulerIndex)
        self.logger.info(msg)

    def schedulerGet(self):
        message = bytearray()
        self.send(self._SCHEDULER_GET, message)
        msg = "Get Scheduler"
        self.logger.info(msg)
    
    def __scheduler_action_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        dataLength = len(message.data)
        data = message.data
        if message is None or message.data is None:
            logstr += " Scheduler Action Status: message is None!!"
        elif dataLength < 10:
            logstr += " Scheduler Action Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
        else:
            logstr += " Scheduler Action Status: "
            index = data[0] & 0xf
            y = data[0] >> 4 | (data[1] << 4) & 0x7f
            m = data[1] >> 3 | (data[2] << 5) & 0x0fff
            d = data[2] >> 7 | (data[3] << 1) & 0x1f
            h = data[3] >> 4 | (data[4] << 4) & 0x1f
            i = data[4] >> 1 & 0x3f
            s = data[4] >> 7 | (data[5] << 1) & 0x3f
            dayOfWeek = data[5] >> 5 | (data[6] << 3) & 0x7f
            action = data[6] >> 4 & 0x0f
            
            self.last_cmd_resp_dict[dongleUnicastAddress] = {"action":action}
            transitionTime = data[7]
            sceneNumber = data[9] * 256 + data[8]

            logstr += "Scheduler " + str(index) + "--"
            if y > 0x64:
                yStr = "Unknown "
            else:
                yStr = "Any year" if y == 0x64 else str(y + 2000)
            logstr += "year:" + yStr + " "
            if m > 0x0FFF:
                mStr = "Unknown "
            else:
                mStr = ""
                j = 0
                while j < 12:
                    if m >> j & 1 == 1:
                        mStr += self.__scheduler_month[j]
                    j += 1
            logstr += "month:" + mStr + " "
            if d > 0x1F:
                dStr = "Unknown "
            else:
                dStr = "Any day" if d == 0 else str(d)
            logstr += "day:" + dStr + " "
            if h > 0x19:
                hStr = "Unknown "
            elif h == 0x19:
                hStr = "Once a day (at a random hour)"
            else:
                hStr = "Any hour of the day" if h == 0x18 else ('%02d' % h)
            logstr += "hour:" + hStr + " "
            if i > 0x3F:
                iStr = "Unknown "
            elif i == 0x3F:
                iStr = "Once an hour (at a random minute)"
            elif i == 0x3E:
                iStr = "Every 20 minutes (minute modulo 20 is 0) (0, 20, 40)"
            elif i == 0x3D:
                iStr = "Every 15 minutes (minute modulo 15 is 0) (0, 15, 30, 45)"
            else:
                iStr = "Any minute of the hour" if i == 0x3C else ('%02d' % i)
            logstr += "minute:" + iStr + " "
            if s > 0x3F:
                iStr = "Unknown "
            elif s == 0x3F:
                iStr = "Any second of the minute"
            elif s == 0x3E:
                iStr = "Every 20 seconds (minute modulo 20 is 0) (0, 20, 40)"
            elif s == 0x3D:
                sStr = "Every 15 seconds (minute modulo 15 is 0) (0, 15, 30, 45)"
            else:
                sStr = "Any second of the minute" if s == 0x3C else ('%02d' % s)
            logstr += "second:" + sStr + " "
            if dayOfWeek > 0x7F:
                dowStr = "Unknown "
            else:
                dowStr = ""
                j = 0
                while j < 7:
                    if dayOfWeek >> j & 1 == 1:
                        dowStr += self.__scheduler_week[j]
                    j += 1
            logstr += "dayOfWeek:" + dowStr + " "
            actionStr = "Unknown " if (str(action) not in self.__scheduler_actions.keys()) \
            else self.__scheduler_actions[str(action)]
            logstr += "action:" + actionStr + " "
            logstr += "transitionTime:" + str(TransitionTime.decode(transitionTime)) + "ms "
            logstr += "sceneNumber:" + str(sceneNumber)
            resp = bytearray([index, y, m>>8, m&0xff, d, h, i, s, \
                    dayOfWeek, action, transitionTime, sceneNumber>>8, sceneNumber&0xff])
        self.logger.info(logstr)
        
    def __scheduler_status_handler(self, opcode, message):
        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        resp = message.data if len(message.data) != 2 else bytearray([message.data[1], message.data[0]])
        dataLength = len(message.data)
        if message is None or message.data is None:
            logstr += " Scheduler Status: message is None!!"
        elif dataLength < 2:
            logstr = " Scheduler Status Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
        else:
            logstr += " Scheduler Status: "
            i = 0
            schedulers = message.data[0] + message.data[1] * 256
            activeS = ""
            inActiveS = ""
            while i < 16:
                action = schedulers >> i & 1
                if action == 1:
                    activeS += str(i) + " "
                else:
                    inActiveS += str(i) + " "
                i += 1
            logstr += "Active Scheduler:" + (activeS if activeS != "" else "None") + ", "
            logstr += "Inactive Scheduler:" + (inActiveS if inActiveS != "" else "None")

        self.logger.info(logstr)

    def schedulerActionSet(self, index, year, month, day, hour, minute, second, \
        dayOfWeek, action, transitionTime, sceneNumber, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<BBBBBBBBH", (index | (year << 4)) & 0xFF, \
            # year & 0x7 << 5 | (month >> 7 & 0x1F), month << 1 & \
            (year >> 4 | (month << 3)) & 0xFF, (month >> 5 | day << 7) & 0xFF, \
            (day >> 1 | (hour << 4)) & 0xFF, (hour >> 4 | minute << 1 | second << 7) & 0xFF, \
            (second >> 1 | (dayOfWeek << 5)) & 0xFF, (dayOfWeek >> 3 | action << 4) & 0xFF, \
            transitionTime, sceneNumber)
        logstr = "Set Scheduler "
        logstr += str(index) + ("" if ack else " Unacknowledged") + "--"
        if year > 0x64:
            yStr = "Unknown "
        else:
            yStr = "Any year" if year == 0x64 else str(year + 2000)
        logstr += "year:" + yStr + " "
        if month > 0x0FFF:
            mStr = "Unknown "
        else:
            mStr = ""
            j = 0
            while j < 12:
                if month >> j & 1 == 1:
                    mStr += self.__scheduler_month[j]
                j += 1
        logstr += "month:" + mStr + " "
        if day > 0x1F:
            dStr = "Unknown "
        else:
            dStr = "Any day" if day == 0 else str(day)
        logstr += "day:" + dStr + " "
        if hour > 0x19:
            hStr = "Unknown "
        elif hour == 0x19:
            hStr = "Once a day (at a random hour)"
        else:
            hStr = "Any hour of the day" if hour == 0x18 else ('%02d' % hour)
        logstr += "hour:" + hStr + " "
        if minute > 0x3F:
            iStr = "Unknown "
        elif minute == 0x3F:
            iStr = "Once an hour (at a random minute)"
        elif minute == 0x3E:
            iStr = "Every 20 minutes (minute modulo 20 is 0) (0, 20, 40)"
        elif minute == 0x3D:
            iStr = "Every 15 minutes (minute modulo 15 is 0) (0, 15, 30, 45)"
        else:
            iStr = "Any minute of the hour" if minute == 0x3C else ('%02d' % minute)
        logstr += "minute:" + iStr + " "
        if second > 0x3F:
            iStr = "Unknown "
        elif second == 0x3F:
            iStr = "Any second of the minute"
        elif second == 0x3E:
            iStr = "Every 20 seconds (minute modulo 20 is 0) (0, 20, 40)"
        elif second == 0x3D:
            sStr = "Every 15 seconds (minute modulo 15 is 0) (0, 15, 30, 45)"
        else:
            sStr = "Any second of the minute" if second == 0x3C else ('%02d' % second)
        logstr += "second:" + sStr + " "
        if dayOfWeek > 0x7F:
            dowStr = "Unknown "
        else:
            dowStr = ""
            j = 0
            while j < 7:
                if dayOfWeek >> j & 1 == 1:
                    dowStr += self.__scheduler_week[j]
                j += 1
        logstr += "dayOfWeek:" + dowStr + " "
        actionStr = "Unknown " if (str(action) not in self.__scheduler_actions.keys()) \
        else self.__scheduler_actions[str(action)]
        logstr += "action:" + actionStr + " "
        logstr += "transmitionTime:" + str(TransitionTime.decode(transitionTime)) + "ms "
        logstr += "sceneNumber:" + str(sceneNumber)
        if ack:
            self.send(self._SCHEDULER_ACTION_SET, message)
            self.logger.info(logstr)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self._SCHEDULER_ACTION_SET_UNACKNOWLEDGED, message)
                self.logger.info(logstr + " repeat:" + str(i))
                i -= 1
