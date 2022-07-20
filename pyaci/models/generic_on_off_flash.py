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


class GenericOnOffFlashClient(Model):
    GENERIC_ON_OFF_FLASH_SET = Opcode(0x82F2, None, "Generic OnOffFlash Set")
    GENERIC_ON_OFF_FLASH_SET_UNACKNOWLEDGED = Opcode(0x82F0, None, "Generic OnOffFlash Set Unacknowledged")
    GENERIC_ON_OFF_FLASH_GET = Opcode(0x82F1, None, "Generic OnOffFlash Get")
    GENERIC_ON_OFF_FLASH_STATUS = Opcode(0x82F4, None, "Generic OnOffFlash Status")

    def __init__(self):
        self.opcodes = [
            (self.GENERIC_ON_OFF_FLASH_STATUS, self.__generic_on_off_flash_status_handler)]
        self.__tid = 0
        super(GenericOnOffFlashClient, self).__init__(self.opcodes)
        self.last_cmd_resp_dict = {}

    def set(self, value, transition_time_ms=10, delay_ms=0, ack=False, repeat=3):
        message = bytearray()
        message += struct.pack("<BBBB", value, self._tid,transition_time_ms,delay_ms)

        # if transition_time_ms > 0:
        #     message += TransitionTime.pack(transition_time_ms, delay_ms)

        if ack:
            self.send(self.GENERIC_ON_OFF_FLASH_SET, message)
            msg = "Turn " + str(value) + " Unacknowledged, "
            msg += "Transition time:" + str(transition_time_ms) + " ms, "
            msg += "Delay time:" + str(delay_ms) + " ms"
            self.logger.info(msg)
        else:
            i = repeat
            while i > 0:
                time.sleep(0.5)
                self.send(self.GENERIC_ON_OFF_FLASH_SET_UNACKNOWLEDGED, message)
                msg = "Turn " +  str(value) + " Unacknowledged, "
                msg += "Transition time:" + str(transition_time_ms) + " ms, "
                msg += "Delay time:" + str(delay_ms) + " ms, "
                msg += "Repeat:" + str(i)
                self.logger.info(msg)
                i -= 1

    def get(self):
        self.send(self.GENERIC_ON_OFF_FLASH_GET)
        self.logger.info("Get Light On Off FLASH Status")

    @property
    def _tid(self):
        tid = self.__tid
        self.__tid += 1
        if self.__tid >= 255:
            self.__tid = 0
        return tid

    def __generic_on_off_flash_status_handler(self, opcode, message):

        dongleUnicastAddress = message.meta['src']
        logstr = "Source Address: " + str(dongleUnicastAddress)
        self.__currentOnOffStatus = "on " if message.data[0] > 0 else "off "
        logstr += " Present OnOff: " + self.__currentOnOffStatus

        self.last_cmd_resp_dict[message.meta['src']] = message.data[0]

        if len(message.data) >= 2:
            logstr += " Target OnOff: " + ("on " if message.data[1] > 0 else "off ")
        if len(message.data) == 3:
            logstr += " Remaining time: %d ms" % (TransitionTime.decode(message.data[2]))
        self.logger.info(logstr)
