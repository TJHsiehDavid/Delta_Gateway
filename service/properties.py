import sys
import os
this_file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,this_file_dir+'/..')
import globalvar as gl

class Proerties:
	# dongle location
	# dev_com = '/dev/tty.usbserial-DN064DB0'
	# dev_baudrate = 1000000
	# port = 8088
	dev_com = gl.get_value('DEV_COM')
	dev_baudrate = gl.get_value('DEV_BAUDRATE')
	port = gl.get_value('PORT')
