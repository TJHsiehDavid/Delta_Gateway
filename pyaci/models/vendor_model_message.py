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


class VendorModelMessageClient(Model):
    VENDOR_MODEL_MESAGE_UNACKNOWLEDGED = Opcode(0xC0, 0x069E, "VENDOR MODEL MESAGE UNACKNOWLEDGED")
    VENDOR_MODEL_MESAGE_GET = Opcode(0xC1, 0x069E, "VENDOR MODEL MESAGE Get")
    VENDOR_MODEL_MESAGE_STATUS = Opcode(0xC2, 0x069E, "VENDOR MODEL MESAGE Status")

    def __init__(self):
        self.opcodes = [
            (self.VENDOR_MODEL_MESAGE_STATUS, self.__vendor_model_message_status_handler)]
        self.__tid = 0
        super(VendorModelMessageClient, self).__init__(self.opcodes)

        self.last_cmd_resp_dict = {}

    def set(self, value):
        message = bytearray()
        message += struct.pack("<BBBBB",0x01,0x00,0x01, value, self._tid)
#Created Access PDU C0 9E 06 01 00 01 01 (對數)
#Created Access PDU C0 9E 06 01 00 01 09 (線性)
        self.send(self.VENDOR_MODEL_MESAGE_UNACKNOWLEDGED, message)
        self.logger.info("VendorModelMessageClient set send")

    def get(self, transition_time_ms=10, delay_ms=0):
        message = bytearray()
        message += struct.pack("<BB",0x01,0x00)
#Created Access PDU C1 9E 06 01 00
        self.send(self.VENDOR_MODEL_MESAGE_GET,message)
        self.logger.info("VendorModelMessageClient get send")

    @property
    def _tid(self):
        tid = self.__tid
        self.__tid += 1
        if self.__tid >= 255:
            self.__tid = 0
        return tid


    def __vendor_model_message_status_handler(self, opcode, message):

        dongleUnicastAddress = message.meta['src']
        logstr = "__vendor_model_message_status_handler "
        logstr += "Source Address: " + str(dongleUnicastAddress)
        data = ['%02x' % b for b in message.data]
        output = ""
        if len(data) >= 4:
            if str(data[3]) == "09":
                output = "linear"
            elif str(data[3]) == "01":
                output = "log"
        logstr += " output: " + output
        # logstr += "message.data[0]: " + str(message.data[0])
        # self.__currentOnOffStatus = "on " if message.data[0] > 0 else "off "
        # logstr += " Present OnOff: " + self.__currentOnOffStatus
        #
        self.last_cmd_resp_dict[message.meta['src']] = output
        #
        # if len(message.data) >= 2:
        #     logstr += " Target OnOff: " + ("on " if message.data[1] > 0 else "off ")
        # if len(message.data) == 3:
        #     logstr += " Remaining time: %d ms" % (TransitionTime.decode(message.data[2]))
        self.logger.info(logstr)