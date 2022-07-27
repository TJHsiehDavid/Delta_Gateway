#!/usr/bin/env python
# coding=utf-8

import os
import datetime
import subprocess, time, sys

#app名字string.
proc_name = 'app.py'
time_allow = 60
sdk_dir = os.path.dirname(os.path.abspath(__file__))
python_compiler_dir = '/usr/local/bin/python3.8'
app_dir = os.path.dirname(os.path.abspath(__file__))

class watchdog():
    def __init__(self, sleep_time, cmd):
        self.time_allow = time_allow
        self.proc = proc_name
        self.ext = (proc_name[-3:]).lower()        #判斷文件的後綴名，全部換成小寫
        self.p = None                              #self.p爲subprocess.Popen()的返回值，初始化爲None


    def log(self, str):
        p = open('proc.log', 'a+')
        p.write('%s  %s \n' % (str, datetime.datetime.now()))
        p.close()


    def watchdog(self):
        ''' check proc有無啟動
            有：返回 1， 沒有：返回 0
        '''
        global app_dir
        app_dir = sdk_dir + '/' + proc_name

        ps_str = 'ps aux |grep %s | grep -v grep' %proc_name
        cmd_dir = os.popen(ps_str).read().split()
        if len(cmd_dir) > 0:
            #print(cmd_dir[-1])
            if cmd_dir[-1] == app_dir:
                return 1
            else:
                return 0
        else:
            return 0




    def restart_proc(self, proc_name):
        '''restart the process that we defined. '''
        self.log('WatchDog-----GW restart %s' % app_dir)
        #print('program restart.')

        ps_str = 'ps aux |grep %s | grep -v grep' % proc_name
        x = os.popen(ps_str).read()

        if self.ext == '.py':
            try:
                self.p = subprocess.Popen([python_compiler_dir, '%s' % app_dir], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, shell=False)
            except:
                pass



def main(object):
    object.log('==== WatchDog boot.====')
    try:
        while 1:
            if object.watchdog() == 0:
                object.restart_proc(proc_name)
            #else:
            #    print('ok, program well')
            time.sleep(60)
    except KeyboardInterrupt as e:
        object.log('==== WatchDog external interrupt.====')
        print("檢測到CTRL+C，準備退出程序!")



if __name__ == '__main__':
    wcd = watchdog(time_allow, proc_name)
    main(wcd)
