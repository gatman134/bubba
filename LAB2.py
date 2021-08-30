#!/usr/bin/python
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



def setGCmd(command):
    global table_cmd
    with trl:
        table_cmd=command
    return
def getGCmd():
    global table_cmd
    with trl:
        return table_cmd
def setGFan(fan):
    global table_fan
    with trl:
        table_fan=fan
    return
def getGFan():
    global table_fan
    with trl:
        return table_fan
def setGHTmp(htemp):
    global table_htemp
    with trl:
        table_htemp=htemp
    return
def getGHTmp():
    global table_htemp
    with trl:
        return table_htemp
def setGLTmp(ltemp):
    global table_ltemp
    with trl:
        table_ltemp=ltemp
    return
def getGLTmp():
    global table_ltemp
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
def networkClient():
    print("Started Network client")
     #initial connection ready, now run continuously
    
    while True:
        #receive command; command packet=="command: <command>" , where command=(-1==FANOFF, -2==FANON,temp==tempSetpoint)
        msg = "Temp: "+str(getGVoltage())
        snd(clientsocket,msg)
        serverPkt = rcv(clientsocket)
        if(len(serverPkt.split()) == 1):
          setGCmd(0)
        else:
          setGCmd(int(serverPkt.split()[1]))

        time.sleep(0.5)
         

def gpioMainClient():
    print("Started GPIO client")
    while True:
        temp = adc.read_adc(channel=0, gain=GAIN, data_rate=128)
        setGVoltage(temp)
        cmd = getGCmd()
        now = datetime.now();
        today = now.strftime("%Y-%m-%d %H:%M:%S")
        
        fanCtrl(temp, cmd)
        setpoint = getGSetpoint()
        fan = getGFan()
        if fan == 1:
            subprocess.run(["sudo", "/usr/sbin/uhubctl", "-l", "2", "-a", "1"], stdout = subprocess.DEVNULL)
            print(today,", Setpoint="+str(setpoint), ", temp="+str(temp), ", fan=ON")
        if fan == 0:
            subprocess.run(["sudo", "/usr/sbin/uhubctl", "-l", "2", "-a", "0"], stdout = subprocess.DEVNULL)
            print(today,", Setpoint="+str(setpoint), ", temp="+str(temp), ", fan=OFF")
        if fan == 2:
            subprocess.run(["sudo", "/usr/sbin/uhubctl", "-l", "2", "-a", "1"], stdout = subprocess.DEVNULL)
            print(today,", Setpoint=internal="+str(setpoint), ", temp="+str(temp), ", fan=ON")
        if fan == 3:
            subprocess.run(["sudo", "/usr/sbin/uhubctl", "-l", "2", "-a", "0"], stdout = subprocess.DEVNULL)
            print(today,", Setpoint=internal="+str(setpoint), ", temp="+str(temp), ", fan=OFF")
        time.sleep(1)
        
def rcv(clientsocket):
    recPkt = clientsocket.recv(1024)
    msg = recPkt.decode('ascii')
    return str(msg)
def snd(clientsocket, msg2send):
    clientsocket.send(msg2send.encode('ascii'))
    return
def fanCtrl(temp, cmd):
    if int(cmd) == -1:
        setGFan(0)
        setGSetpoint("FAN_OFF")
        return
    if int(cmd) == -2:
        setGFan(1)
        setGSetpoint("FAN_ON")
        return
    if int(cmd) == 0:
        if temp > getGSetpoint():
            setGSetpoint(26337)
            setGFan(2)
        if temp < getGSetpoint():
            setGSetpoint(26337)
            setGFan(3)
        return
    else:
        setGSetpoint(cmd)
        if temp > int(getGSetpoint()):
            setGFan(1)
        if temp < int(getGSetpoint()):
            setGFan(0)

trl=threading.RLock()
GAIN=1
adc=Adafruit_ADS1x15.ADS1115()
setGFan(2)
setGCmd(0)
setGLTmp(26300)
setGHTmp(26350)
setGSetpoint(26337)
clientsocket = socket(AF_INET, SOCK_STREAM)
try:
    clientsocket.connect(('localhost', 4000))
except socket:
    print("Error: socket.error")
    os._exit(0)
except: 
    print("Error: general connection error")
    os._exit(0)
print("connected!")
msg = "Node: 2";
snd(clientsocket,msg)
rcv(clientsocket)

temp = adc.read_adc(channel=0, gain=GAIN, data_rate=128)
setGVoltage(temp)
msg = "Temp: "+str(getGVoltage())+" "+str(getGLTmp())+" "+str(getGHTmp());
snd(clientsocket,msg)
rcv(clientsocket)
time.sleep(2)
print("To quit remote, press CTRL-C")

if __name__ == "__main__":
    print("starting..")
    thread1 = threading.Thread(target = networkClient )
    thread2 = threading. Thread(target = gpioMainClient )
    try:
        thread1.start()
        thread2.start()
    except KeyboardInterrupt:
        thread1.join()
        theard2.join()
        os._exit(0)
