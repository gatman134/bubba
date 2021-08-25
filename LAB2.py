# Program By Daniel batista
# Made for the Adafruit_ADS1x15
# Fan controller for maintaining thermistor temperature

import time
from socket import *
from datetime import datetime
import Adafruit_ADS1x15
import subprocess
import os
import sys
import errno
import threading
global fan

trl=threading.RLock()
GAIN=1
adc=Adafruit_ADS1x15.ADS1115()

def setGCmd(command):
    global table_cmd
    with trl:
        table_cmd=command
    return
def getGCmd():
    global table_cmd
    with trl:
        return table_cmd
def setGHTmp(htemp):
    global table_htmp
    with trl:
        table_htmp=htemp
    return
def getGHTmp():
    global table_htmp
    with trl:
        return table_htemp
def setGLTmp(ltemp):
    global table_ltmp
    with trl:
        table_ltmp=ltemp
    return
def getGLTmp():
    global table_ltmp
    with trl:
        return table_ltemp
def setGVoltage(voltage):
    global table_voltage
    with trl:
        table_voltage=voltage
    return
def getGVoltage():
    global table_voltage
    with trl:
        return table_voltage
def setGSetpoint(setpoint):
    global table_setpoint
    with trl:
        table_setpoint=setpoint
    return
def getGSetpoint():
    global table_setpoint
    with trl:
        return table_setpoint
def networkt():
     #initial connection ready, now run continuously
    running = 1
    while running:
        temp = adc.read_adc(channel=0, gain=GAIN, data_rate=128)
        setGVoltage(temp)
        # Wait for the response from the server
        #receive command; command packet=="command: <command>" , where command=(-1==FANOFF, -2==FANON,temp==tempSetpoint)
        (error, serverPkt) = rcv(clientsocket) #you will receive your command from here
        setGCmd(serverPkt)
        if(error):
            print("ERROR: error after recv")
            running=0
            continue
        #reply to server
        error = snd(clientsocket,"Temp:"+getGVoltage) #you will need to send the temp here
        if(error):
            running=0
            continue
def gpioMainClient():
    while True:
        temp = getGVoltage()
        setpoint = getGSetpoint()
        cmd = getGCmd()
        now = datetime.now();
        today = now.strftime("%Y-%m-%d %H:%M:%S")
        print("To exit the program please use CTRL+C")
        fan = fanCtrl(temp, cmd)
        if fan == 1:
            ON = os.system("sudo uhubctl -l 2 -a 1")
            print(today,", Setpoint ="+str(set_temp), ", temp ="+str(temp), ", fan =ON")
        if fan == 0:
            OFF = os.system("sudo uhubctl -l 2 -a 0")
            print(today,", Setpoint ="+str(set_temp), ", temp ="+str(temp), ", fan =OFF")
        time.sleep(2)
def rcv(clientsocket):
 msg=""
 error=False
 try:
    recPkt = clientsocket.recv(1024)
    msg = recPkt.decode('ascii')
 #except socket.error as msg:
 # print "Socket Error: %s" % msg
 except TypeError as msg:
    logit(getTs()+" Connection "+outit(clientaddress, "")+" -- Error: TypeError non-integer")
    error=False
 except:
    logit(getTs()+" Connection "+outit(clientaddress, "")+" -- Error: socket receive, dropping connection")
    error=True
    return (error, str(msg))
def snd(clientsocket, msg2send):
 error=False
 msg=""
 try:
    clientsocket.send(msg2send.encode('ascii'))
 #except socket.error, msg:
 except socket as msg:
    logit(getTs()+" Connection "+outit(clientaddress, "")+" -- Error: socket send, dropping connection")
    error=True
 except:
    logit(getTs()+" Connection "+outit(clientaddress, "")+" -- Error: general send, dropping connection")
    error=True
 return (error) 
def fanCtrl(temp, cmd):
    if int(cmd) == -1:
        fan = 1
    if int(cmd) == -2:
        fan = 0
    if cmd == ""
        if temp > getGSetpoint():
            fan = 1
        if temp < getGSetpoint():
            fan = 0
setGLtmp()
clientsocket = socket(AF_INET, SOCK_STREAM)
try:
    clientsocket.connect(('localhost', 4000))
except socket:
    print("Error: socket.error")
    os._exit(0)
except: 
    print("Error: general connection error")
    os._exit(0)
print("connected! To quit remote, press CTRL-C")
msg = "NODE: "+str(0);
error = snd(clientsocket,msg)
if(error):
    clientsocket.close()
error = rcv(clientsocket)
if(error):
    clientsocket.close()
print("Please enter the wait time between: ")
    msg = "Temp: "+str(getGVoltage())+" "+str(getGLTmp())+" "+str(getGHTmp());
    error = snd(clientsocket,msg)
    if(error):
        clientsocket.close()
    error = rcv(clientsocket)
    if(error):
        clientsocket.close()

if __name__ == "__main__":
    print("starting..")
    empty1=""
    empty2=""
    setGisReady(False)
    networkt=threading.Thread(target = netThread, args = (empty1, empty2))
    try:
        networkt()
        gpioMainClient()
    except KeyboardInterrupt:
        os._exit(0)
