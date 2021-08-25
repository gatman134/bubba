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
def setGLTmp(htemp):
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
    temp = getGVoltage()
    cmd = getGCmd()
    print("To exit the program please use CTRL+C")
    fan = fanCtrl(temp, cmd)
    if (fan == 1):
        ON = os.system("sudo uhubctl -l 2 -a 1")
    else:
        OFF = os.system("sudo uhubctl -l 2 -a 0")
    time.sleep(int(wait_time))
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
wait_time = input();
loop = True
while loop:
    print("Please enter the setpoint (Must be between 26330-26340): ")
    try:
        set_temp = int(input());
    except ValueError:
        print("Please enter a integer")
        continue
    if  (set_temp > 26340) or(set_temp < 26330) :
        print("Please enter between 26330-26340: ")
        continue
    else:
        loop = False
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
