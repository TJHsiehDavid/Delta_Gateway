#!/usr/bin/env python
# coding=utf-8

import os
import datetime
import subprocess, time, sys

#app名字string.
proc_name = 'app.py'
time_allow = 60


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
        ps_str = 'ps aux |grep %s | grep -v grep' %proc_name
        x = os.popen(ps_str).read()
        print(x)

        if x == '':
            return 1
        else:
            return 0


    def restart_proc(self, proc_name):
        '''restart the process that we defined. '''
        self.log('WatchDog-----GW restart app.py')
        print('program restart.')

        ps_str = 'ps aux |grep %s | grep -v grep' % proc_name
        x = os.popen(ps_str).read()

        if x and self.ext == '.py':
            print('process is functioning normally.')
        else:
            #沒有找到特定程序,直接啟動該程序
            try:
                self.p = subprocess.Popen(['python3.8', '%s' % self.proc], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, shell=False)
            except:
                pass



def main(object):
    object.log('==== WatchDog boot.====')
    try:
        while 1:
            if object.watchdog():
                object.restart_proc(proc_name)
            else:
                print('ok, program well')
            time.sleep(300)
    except KeyboardInterrupt as e:
        object.log('==== WatchDog external interrupt.====')
        print("檢測到CTRL+C，準備退出程序!")



if __name__ == '__main__':
    wcd = watchdog(time_allow, proc_name)
    main(wcd)
