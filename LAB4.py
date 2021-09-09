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
    global connected
    msg="on connect userdata="+str(userdata)+", flags="+str(flags)+", rc="+str(rc)
    if(rc==0):
        connected = True
        (error, mID) = client.subscribe(topic,0) #SUBSCRIBE HERE
        if(not error==0):
            MQTT_error = " -- not discernible"
            if str(error) in mqtterr.keys():
                MQTT_error = mqtterr.get(str(error))
            msg="client.subscribe error, error="+str(error)+", MQTT_ERROR="+MQTT_error
            print(msg)
    
    return
def on_message(client, userdata, message): #separate thread
    now = datetime.now();
    today = now.strftime("%Y-%m-%d %H:%M:%S")
    #commXhrl = { '':"No Command", '-1':"FAN OFF", '-2' }
    payload=message.payload.decode('ascii')
    payload_list = payload.split(',')
    if message.topic == "rUI/command/4/remoteUI-default":
        setGCmd(payload[0])
        setGTime(payload[1])
    print(message.topic+"  "+payload)
    topic ="nodes/command/4"
    payload1 = payload[0]+","+today
    mqttc.publish(topic, payload1)
    time.sleep(1)

    
        
def on_subscribe(client, userdata, mid, granted_qos):
    msg="on subscribe: userdata="+str(userdata)+", mid="+str(mid)+",granted_qos="+str(granted_qos)
    print(msg)
    return
def on_publish(client,userdata,result): #create function for callback
    msg=("DEBUG: on_publish(): client=="+str(client)+"==, userdata=="+str(userdata)+"==,result=="+str(result)+"==eol")
def setGTime(time):
    global table_time
    with trl:
        table_time=time
    return
def getGTime():
    global table_time
    with trl:
        return table_time
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
    if cmd == -1:
        setGFan(0)
        setGSetpoint("FAN_OFF")
        return
    if cmd == -2:
        setGFan(1)
        setGSetpoint("FAN_ON")
        return
    if cmd == "":
        if temp > getGSetpoint():
            setGSetpoint(26337)
            setGFan(2)
        if temp < getGSetpoint():
            setGSetpoint(26337)
            setGFan(3)
        return
    if cmd.isdigit() == False:
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
setGCmd(0)
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
            mqttc.connect("localhost")
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
