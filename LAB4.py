#!/usr/bin/python
# Program By Daniel batista
# Made for the Adafruit_ADS1x15
# Fan controller for maintaining thermistor temperature

import time
import paho.mqtt.client as mqtt
from socket import *
from datetime import datetime
import Adafruit_ADS1x15
import subprocess
import os
import sys
import errno
import threading

def on_connect(client, userdata, flags, rc):
    print("Client is connected to node 4")
    return
def on_message(client, userdata, message): #separate thread
    print("[Received] Topic: " + message.topic + ", Message: " + message.payload.decode())
    now = datetime.now();
    today = now.strftime("%Y-%m-%d %H:%M:%S")
    #commXhrl = { '':"No Command", '-1':"FAN OFF", '-2' : "FAN ON" }
    payload=message.payload.decode()
    setGCmd(str(payload.split(',')[0]))
    topic ="nodes/command/4"
    payload1 = str(payload.split(',')[0])+","+today
    mqttc.publish(topic, payload1)
    time.sleep(.1)        
def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed")
    return
def on_publish(client,userdata,result): #create function for callback
    msg=("DEBUG: on_publish(): client=="+str(client)+"==, userdata=="+str(userdata)+"==,result=="+str(result)+"==eol")
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

def gpioMainClient():
    print("Started GPIO client")
    while True:
        #receive command; command packet=="command: <command>" , where command=(-1==FANOFF, -2==FANON,temp==tempSetpoint)
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
        topic = "nodes/temp/4"
        #payload = ”<temp>_<lowRange>_<highRange>,<setTime>”
        payload = str(getGVoltage()) + "_" + str(getGLTmp())+"_"+str(getGHTmp())+","+today
        mqttc.publish(topic, payload)
        time.sleep(1)
        
def fanCtrl(temp, cmd):
    if cmd == "-":
        return
    if cmd == '':
        setGSetpoint(26337)
        if temp > int(getGSetpoint()):
            setGFan(2)
        if temp < int(getGSetpoint()):
            setGFan(3)
        return    
    if int(cmd) == -1:
        setGFan(0)
        setGSetpoint("FAN_OFF")
        return
    if int(cmd) == -2:
        setGFan(1)
        setGSetpoint("FAN_ON")
        return

    else:
        setGSetpoint(int(float(cmd)))
        if temp > int(getGSetpoint()):
            setGFan(1)
        if temp < int(getGSetpoint()):
            setGFan(0)

trl=threading.RLock()
GAIN=1
adc=Adafruit_ADS1x15.ADS1115()
setGFan(2)
setGCmd('')
setGLTmp(26300)
setGHTmp(26350)
setGSetpoint(26337)
topic= "#"
host = "localhost"
myport=1883
temp = adc.read_adc(channel=0, gain=GAIN, data_rate=128)
setGVoltage(temp)
print("To quit remote, press CTRL-C")

if __name__ == "__main__":
    print("starting..")
    
    thread = threading. Thread(target = gpioMainClient )
    try:
        mqttc = mqtt.Client()
        mqttc.on_message = on_message
        mqttc.on_connect = on_connect
        mqttc.on_publish = on_publish
        mqttc.on_subscribe = on_subscribe
        thread.start()
        
        print("Connecting to " + host + "/" + topic)
        try:
            mqttc.connect('localhost')
            #mqttc.connect("ec2-54-193-32-216.us-west-1.compute.amazonaws.com")
            mqttc.subscribe("rUI/command/4/#")
            mqttc.loop_start()
        except Exception as e:
            print("Error: exception -- error was: "+str(e))
            thread.join()
            mqttc.loop_stop()
            os._exit(0)

    except KeyboardInterrupt:
        thread.join()
        mqttc.loop_stop()
        os._exit(0)
