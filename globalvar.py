import os
from configparser import ConfigParser

global_dict = {}

device_dict = {}

# global_dict["DEV_COM"] = "/dev/tty.usbserial-DN064DB0"
# global_dict["DEV_BAUDRATE"] = 1000000
# global_dict["PORT"] = 8088

# 控燈後是否會寫回狀態(True:會寫入DB,False:不會寫入DB)
global_dict["testSaveDb"] = True

#是否會訂閱Group(True:會Subscription ,False:不會Subscription)
global_dict["SUB_STATUS"] = False

#收到RX,是否更新回裝置的狀態(True:會更新,False:不會更新)
global_dict["updateDeviceStatus"] = True

#是否印出log(True:會印,False:不會印)(僅部分程式有使用此變數)
global_dict["MORE_LOG"] = False

#確認process是否開好了(only process can change.)
global_dict["PROCESS_READY"] = False

#藍芽指令的TTL
global_dict["TTL"] = 8

def write_config_ini():
    sdk_dir = os.path.dirname(os.path.abspath(__file__))
    config = ConfigParser()
    config.read(sdk_dir + '/config.ini')
    config.set("DEFAULT", "SUB_STATUS", str(global_dict["SUB_STATUS"]))
    config.set("DEFAULT", "MORE_LOG", str(global_dict["MORE_LOG"]))
    config.set("DEFAULT", "TTL", str(global_dict["TTL"]))
    config.set("DEFAULT", "DEV_COM", str(global_dict["DEV_COM"]))
    config.set("DEFAULT", "DEV_BAUDRATE", str(global_dict["DEV_BAUDRATE"]))
    config.set("DEFAULT", "PORT", str(global_dict["PORT"]))
    config.set("LOCAL_ADDRESS", "PROVISIONERADDRESS", str(global_dict["PROVISIONERADDRESS"]))
    config.set("LOCAL_ADDRESS", "MANUAL_CHANGED", str(global_dict["MANUAL_CHANGED"]))

    hd = open(sdk_dir + '/config.ini', "w")
    config.write(hd)
    hd.close()
    # device_config = ConfigParser()
    # device_config.read(sdk_dir + '/device.ini')
    # device_config.set("DEFAULT", "server_ip", str(global_dict["server_ip"]))
    # device_config.set("DEFAULT", "server_username", str(global_dict["server_username"]))
    # device_config.set("DEFAULT", "server_password", str(global_dict["server_password"]))
    # device_config.set("DEFAULT", "server_sitename", str(global_dict["server_sitename"]))
    # device_config.set("DEFAULT", "server_device_number", str(global_dict["server_device_number"]))
    # device_config.set("DEFAULT", "server_device_lost_sec", str(global_dict["server_device_lost_sec"]))
    # device_config.set("DEFAULT", "server_device_check_lost_every_sec", str(global_dict["server_device_check_lost_every_sec"]))

def read_config_ini():
    sdk_dir = os.path.dirname(os.path.abspath(__file__))
    config = ConfigParser()
    config.read(sdk_dir + '/config.ini')
    set_value('SUB_STATUS', config['DEFAULT'].getboolean('SUB_STATUS'))
    set_value('MORE_LOG', config['DEFAULT'].getboolean('MORE_LOG'))
    set_value('TTL', config['DEFAULT'].getint('TTL'))
    set_value('DEV_COM', config['DEFAULT']['DEV_COM'])
    set_value('DEV_BAUDRATE', config['DEFAULT'].getint('DEV_BAUDRATE'))
    set_value('PORT', config['DEFAULT'].getint('PORT'))
    set_value('PROVISIONERADDRESS', config['LOCAL_ADDRESS'].getint('PROVISIONERADDRESS'))
    set_value('MANUAL_CHANGED', config['LOCAL_ADDRESS'].getboolean('MANUAL_CHANGED'))

    device_config = ConfigParser()
    device_config.read(sdk_dir + '/device.ini')
    set_value('server_ip', device_config['DEFAULT']['server_ip'])
    set_value('server_username', device_config['DEFAULT']['server_username'])
    set_value('server_password', device_config['DEFAULT']['server_password'])
    set_value('server_sitename', device_config['DEFAULT']['server_sitename'])
    set_value('server_device_number', device_config['DEFAULT']['server_device_number'])
    set_value('server_device_lost_sec', device_config['DEFAULT'].getint('server_device_lost_sec'))
    set_value('server_device_check_lost_every_sec', device_config['DEFAULT'].getint('server_device_check_lost_every_sec'))
    set_value('server_device_check_lost_onoff', device_config['DEFAULT'].getint('server_device_check_lost_onoff'))
    set_value('server_device_cadence_time_interval_onoff', device_config['DEFAULT'].getint('server_device_cadence_time_interval_onoff'))
    set_value('server_device_cadence_interval', device_config['DEFAULT'].getint('server_device_cadence_interval'))

    print("read_config_ini get_value('SUB_STATUS'):"+str( get_value('SUB_STATUS') ))
    print("read_config_ini get_value('MORE_LOG'):"+str( get_value('MORE_LOG') ))
    print("read_config_ini get_value('TTL'):"+str( get_value('TTL') ))
    print("read_config_ini get_value('DEV_COM'):"+str( get_value('DEV_COM') ))
    print("read_config_ini get_value('DEV_BAUDRATE'):"+str( get_value('DEV_BAUDRATE') ))
    print("read_config_ini get_value('PORT'):"+str( get_value('PORT') ))
    print("read_config_ini get_value('PROVISIONERADDRESS'):" + str(get_value('PROVISIONERADDRESS')))
    print("read_config_ini get_value('MANUAL_CHANGED'):" + str(get_value('MANUAL_CHANGED')))
    print("read_device_ini get_value('server_sitename'):"+str( get_value('server_sitename') ))
    print("read_device_ini get_value('server_device_number'):"+str( get_value('server_device_number') ))
    print("read_device_ini get_value('server_device_lost_sec'):"+str( get_value('server_device_lost_sec') ))
    print("read_device_ini get_value('server_device_check_lost_every_sec'):"+str( get_value('server_device_check_lost_every_sec') ))
    print("read_device_ini get_value('server_device_check_lost_onoff'):" + str(get_value('server_device_check_lost_onoff')))
    print("read_device_ini get_value('server_device_cadence_time_interval_onoff'):" + str(get_value('server_device_cadence_time_interval_onoff')))
    print("read_device_ini get_value('server_device_cadence_interval'):" + str(get_value('server_device_cadence_interval')))

    device_lists = device_config.items( "device_lists" )
    for key, val in device_lists:
        print("read_config_ini key:" + str(key) + " val:"+str(val))
        device_dict[str(key)] = str(val).replace("BV", "")

def read_env():
    # 使用雙 dongle 啟動雙 server 時,不可設定 --DEV_COM=/dev/tty.usbserial-DN064DB0 --DEV_BAUDRATE=1000000 --PORT=8088
    # export BIC_SDK="--DEV_COM=/dev/tty.usbserial-DN064DB0 --DEV_BAUDRATE=1000000 --PORT=8088 --SUB_STATUS=False --MORE_LOG=True --TTL=8"
    BIC_SDK = str(os.getenv('BIC_SDK'))
    print("os.getenv('BIC_SDK'):"+BIC_SDK)
    if BIC_SDK != None:
        env_list = BIC_SDK.split('--')
        for item in env_list:
            item2 = item.strip().split('=')
            if len(item2) == 2:
                if item2[1] == "True":
                    print("read_env "+item2[0]+":True")
                    set_value(item2[0], True)
                elif item2[1] == "False":
                    print("read_env "+item2[0]+":False")
                    set_value(item2[0], False)
                elif item2[1].isdigit():
                    print("read_env "+item2[0]+":"+item2[1])
                    set_value(item2[0], int(item2[1]))
                else:
                    print("read_env "+item2[0]+":"+item2[1])
                    set_value(item2[0], item2[1])



def set_value(name, value):
    global_dict[name] = value

def get_value(name, defValue=None):
    try:
        return global_dict[name]
    except KeyError:
        return defValue

def get_object_reference(name, defValue=None):
    try:
        return device_dict[name]
    except KeyError:
        return defValue