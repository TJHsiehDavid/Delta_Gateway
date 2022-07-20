# Enviroment:<br>
###Linux:<br>
Raspbian GNU/Linux 10 (buster)<br>
Python version:<br>
3.9.6<br>
pip version:<br>
pip 21.2.4 from /home/pi/.pyenv/versions/3.9.6/lib/python3.9/site-packages/pip (python 3.9)<br>

###MacOS:<br>
macOS Big sur 11.6<br>
Python version:<br>
3.9.6<br>
pip version:<br>
pip 21.2.4 from /Users/liby/.pyenv/versions/3.9.6/lib/python3.9/site-packages/pip (python 3.9)<br>

###Windows:<br>
Windows 7<br>
Python version:<br>
3.8.2<br>
pip version:<br>
pip 21.1.2 from f:\programs\python\python38\lib\site-packages\pip (python 3.8)<br>

---
#1.config.ini Setup<br>
##1.1 Find COM port device node name of OS<br>
###1.1.1 Linux
>ls /dev/tty* 
>
找到 
>/dev/ttyUSB0 
>

###1.1.2 MacOS
>ls /dev/tty* 
>
找到 
>/dev/tty.usbserial-DN064DB0 
>

###1.1.3 Windows直接使用com3(插入電腦時有顯示)

##1.2 Edit COM port device node name
將1.1查出的資料寫入此檔案 , 如有重新下載整包code , 請記得修改此檔案<br>
./config.ini<br>

###1.2.1 Linux:
>dev_com = /dev/ttyUSB0
>
###1.2.2 MacOS:
>dev_com = /dev/tty.usbserial-DN064DB0
>
###1.2.3 Windows:
>dev_com = com3
>

##1.3 Other config in config.ini
>###設定 dongle 的 baudrate<br>
>dev_baudrate = 1000000
>###設定 web server port<br>
>port = 8088
>###設定是否會訂閱Group (True:會訂閱,False:不會訂閱)<br>
>sub_status = False
>###設定是否印出更多的log (True:會印,False:不會印)<br>
>more_log = True
>###設定藍芽指令的TTL <br>
>ttl = 10

##1.4 環境變數設定
#### 此環境變數的設定值優先權高於config.ini,可依照需求設定需要的參數上去即可<br>
(不需全部參數都設定,例如:單一主機跑雙server時,不可設定port)
###1.4.1 Linux:
>export BIC_SDK="--DEV_COM=/dev/ttyUSB0 --DEV_BAUDRATE=1000000 --PORT=8088 --SUB_STATUS=False --MORE_LOG=True --TTL=8"
>
###1.4.2 MacOS:
>export BIC_SDK="--DEV_COM=/dev/tty.usbserial-DN064DB0 --DEV_BAUDRATE=1000000 --PORT=8088 --SUB_STATUS=False --MORE_LOG=True --TTL=8"
>
###1.4.3 Windows:
>set BIC_SDK="--DEV_COM=com3 --DEV_BAUDRATE=1000000 --PORT=8088 --SUB_STATUS=False --MORE_LOG=True --TTL=8"
>


---

#2. Install 3rd party package<br>
>pip install -r requirements.txt
>

---

#3.Import：<br>
##3.1 匯入手機app匯出的json檔案:<br>
###3.1.1 放置檔案：將app匯出的json檔案重新命名(LTDMS.json)，放置在 ./pyaci/data/

###3.1.2 執行匯入指令:<br>
於 ./pyaci/ 執行下列指令(依照取得的dev name)<br>
PS1:如果拿到的是pyc版本的程式,interactive_pyaci.py要改為interactive_pyaci.pyc <br>
PS2: Windows 系統請先看 3.1.2.1
>python interactive_pyaci.py<br> 
>or<br>
>python interactive_pyaci.pyc<br>
>>importConfig(device)<br>
exit()<br>
> 

####3.1.2.1 Windows:<br>
目前 Windows 版本的 IPython Lib 會遇到問題<br>
請修改
\Python\Python38\Lib\site-packages\IPython\utils\timing.py<br>
將 time.clock 取代為 time.time<br>
接著就能執行以上指令<br>


---

#4 Start BICWEB WebAPI application<br>

###請於 ./ 執行下列指令 (非 ./pyaci/ )
PS:如果拿到的是pyc版本的程式,app.py要改為app.pyc <br>

>python app.py<br> 
>or<br>
>python app.pyc<br>


---

#5.Reset Network：<br>
如需要清空裝置,可用<br>
./pyaci/data/LTDMS_empty.json 覆蓋掉 ./pyaci/data/LTDMS.json<br> 
然後做一次匯入的動作即可清空裝置,<br>
如果想重新匯入新的 json , 直接用新的檔案覆蓋 LTDMS.json 再做匯入的動作即可<br>