# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2018, Nordic Semiconductor ASA
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

from mesh.access import Model, Opcode
from models.common import TransitionTime
import struct
import time

class GenericLevelClient(Model):
    GENERIC_LEVEL_GET = Opcode(0x8205, None, "Generic Level Get")
    GENERIC_LEVEL_STATUS = Opcode(0x8208, None, "Generic Level Status")

    GENERIC_LEVEL_SET = Opcode(0x8206, None, "Generic Level Set")
    GENERIC_LEVEL_UNACKNOWLEDGED = Opcode(0x8207, None, "Generic Level Set Unacknowledged")

    GENERIC_LEVEL_DELTA_SET = Opcode(0x8209, None, "Generic Delta Set")
    GENERIC_LEVEL_DELTA_SET_UNACKNOWLEDGED = Opcode(0x820A, None, "Generic Delta Set Unacknowledged")

    GENERIC_LEVEL_MOVE_SET = Opcode(0x820B, None, "Generic Move Set")
    GENERIC_LEVEL_MOVE_SET_UNACKNOWLEDGED = Opcode(0x820C, None, "Generic Move Set Unacknowledged")

    def __init__(self):
        self.opcodes = [
            (self.GENERIC_LEVEL_STATUS, self.__generic_level_status_handler)]
        self.__tid = 0
        self.isCurrentSet = False
        super(GenericLevelClient, self).__init__(self.opcodes)
        self.last_cmd_resp_dict = {}

    def set(self, level, transition_time_ms=0, delay_ms=0, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<hB", level, self._tid)
        if transition_time_ms > 0:
            message += TransitionTime.pack(transition_time_ms, delay_ms)
        if ack:
            self.send(self.GENERIC_LEVEL_SET, message)
            msg = "Set 1 Light/LightTemprate/Current Level To " + str(level)
            msg += ", Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.GENERIC_LEVEL_UNACKNOWLEDGED, message)
                msg = "Set 2 Light/LightTemprate/Current Level To " + str(level)
                msg += " Unacknowledged, Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms, "
                msg += "Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def delta_set(self, delta_level, transition_time_ms=0, delay_ms=0, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<BBBBB", delta_level & 0xff , delta_level >> 8 & 0xff, \
            delta_level >> 16 & 0xff, delta_level >> 24 & 0xff, self._tid)
        if transition_time_ms > 0:
            message += TransitionTime.pack(transition_time_ms, delay_ms)
        if ack:
            self.send(self.GENERIC_LEVEL_DELTA_SET, message)
            msg = "Change Light/LightTemprate/Current Level By " + str(delta_level)
            msg += ", Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.GENERIC_LEVEL_DELTA_SET_UNACKNOWLEDGED, message)
                msg = "Change Light/LightTemprate/Current Level By " + str(delta_level)
                msg += " Unacknowledged, Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms, "
                msg += "Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def move_set(self, delta_level, transition_time_ms=0, delay_ms=0, ack=True, repeat=1):
        message = bytearray()
        message += struct.pack("<hB", delta_level, self._tid)
        if transition_time_ms > 0:
            message += TransitionTime.pack(transition_time_ms, delay_ms)
        if ack:
            self.send(self.GENERIC_LEVEL_MOVE_SET, message)
            msg = "Change Light/LightTemprate/Current Level By " + str(delta_level)
            msg += ", Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.GENERIC_LEVEL_MOVE_SET_UNACKNOWLEDGED, message)
                msg = "Move Light/LightTemprate/Current Level By " + str(delta_level)
                msg += " Unacknowledged, Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms, "
                msg += "Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def get(self):
        self.send(self.GENERIC_LEVEL_GET)
        self.logger.info("Get Light/LightTemprate/Current Level")

    @property
    def _tid(self):
        tid = self.__tid
        self.__tid += 1
        if self.__tid >= 255:
            self.__tid = 0
        return tid

    def __generic_level_status_handler(self, opcode, message):

        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        data = message.data
        dataLen = len(data)
        if dataLen == 2:
            resp = bytearray([data[1], data[0]])
        elif dataLen == 5:
            resp = bytearray([data[1], data[0], data[3], data[2], data[4]])
        else:
            resp = data
        data = ['%02x' % b for b in message.data]
        dataLength = len(data)
        res = False
        if message is None or message.data is None:
            logstr += " Generic Level: message is None!!"
            self.logger.info(logstr)
        elif dataLength < 2:
            logstr += " Generic Level Error: msg=" 
            logstr += ''.join(['%02x' % b for b in message.data])
            self.logger.info(logstr)
        else:
            # present_level, = struct.unpack("<h", message.data[0:2])
            present_level = int(data[1], 16) << 8 | int(data[0], 16)
            if present_level > 32767:
                present_level -= 65536
            self.__currentlevel = present_level
            logstr += " Present Level: " + str(present_level)
            if dataLength >= 4:
                # target_level, = struct.unpack("<h", message.data[2:4])
                target_level = int(data[3], 16) << 8 | int(data[2] ,16)
                logstr += " Target Level: " + str(target_level)
            if dataLength == 5:
                remaining_time = int(data[4], 16)
                logstr += " Remaining time: %d ms" % (TransitionTime.decode(remaining_time))
            self.logger.info(logstr)
            self.last_cmd_resp_dict[dongleUnicastAddress] = present_level

            # add to fix bug
            # print("add to fix bug:" + str(dongleUnicastAddress) + "level")
            self.last_cmd_resp_dict[str(dongleUnicastAddress)+"level"] = present_level
