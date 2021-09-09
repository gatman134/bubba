#!/usr/bin/python3
#!/Library/Frameworks/Python.framework/Versions/3.9/bin/python3  #MACOSX BigSur
#!/usr/local/bin/python
import os
import sys
import time
import datetime
import threading
#import context
import paho.mqtt.client as mqtt #pub temp as client of broker 
import re
#---get mac below
import socket #to get IPADDR for nodename
import fcntl
import struct
import subprocess
#random string of given length
import random
import string
import queue 

from dataclasses import dataclass, field
from typing import Any

#-------global
broker_address="localhost"
broker_address="172.20.105.184"  #SECTION2
broker_address="172.20.109.43"   #SECTION1
broker_address="10.0.0.145"      #Home
#remote_server="ec2-52-15-61-238.us-east-2.compute.amazonaws.com" #AWS
broker_address="ec2-54-193-32-216.us-west-1.compute.amazonaws.com" #AWS
remote_server="ec2-54-193-32-216.us-west-1.compute.amazonaws.com" #AWS
IP=""
qm=[]   #my queued messages from on_message()
ql=[]   #my queued log messages for logit()
running=True
mqttport=1883
NODE="A"   #default
connected = False
BAD=True
GOOD=False
empty=""
empty2=""
tablet=""
maint=""
logFile="remoteLog.txt"
gLL=False   #global lock logfile
try:
    fdw=open(logFile, 'w')
    fdw.write(" --init-- \n")
    fdw.close()
except IOError as e:
    print(ts()+" -- Loging Error found:({})".format(e))
    print("Error: the input file \'"+logFile+"\' does not exist, see -h for help,  ... exiting ...")
logMFile="remoteMLog.txt"
#try:
#    fdmw=open(logMFile, 'w')
#    fdmw.write(" --init-- \n")
#    fdmw.close()
#except IOError as e:
#    print(ts()+" -- Loging Error found:({})".format(e))
#    print("Error: the input file \'"+logMFile+"\' does not exist, see -h for help,  ... exiting ...")
data=""
tsv=""
nodeDB = []
uiDB = []
trl=threading.RLock()
#c=threading.Condition()
availableNodes = [ '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16',
                   '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', 
                   '32', '33', '34' , '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45' ]
commXhrl = { '':"No Command", '-1':"FAN OFF", '-2':"FAN ON" }
commXlater = { '2': "", '3': "-1", '4': "-2", '5': "5" }
stack=[]          #of the form stack==[ (<topic>, <data>), (<"Error">, <msgID>) ]
mqtterr = { '-1':"MQTT_ERR_AGAIN", '0':"MQTT_ERR_SUCCESS", '1':"MQT_ERR_NOMEM", '2':"MQTT_ERR_PROTOCOL", 
        '3': "MQTT_ERR_INVAL", '4': "MQTT_ERR_NO_CONN", '5':"MQTT_ERR_CONN_REFUSED", '6':"MQTT_ERR_NOT_COUND", 
        '7':"MQTT_ERR_CONN_LOST", '8':"MQTT_ERR_TLS", '9':"MQTT_ERR_PAYLOAD_SIZE", '10':"MQTT_ERR_NOT_SUPPORTED", 
        '11':"MQTT_ERR_AUTH", '12':"MQTT_ERR_ACL_DENIED", '13':"MQTT_ERR_UNKNOWN", '14':"MQTT_ERR_ERRNO", 
        '15':"MQTT_ERR_QUEUE_SIZE" }
#topics
ANY="#"  #this is the wild card
BAR="/"
qos=2
class Topic:
    temp="nodes/temp/"      #temp Topic.temp=="nodes/temp/<node>", where node=1,2,3...
    cmd="nodes/command/"    #command node topi.cmd=="nodes/command/<node>", where node=1,2,3...
    rui="rUI/command/"        #Topic.rUI=="rUI/<remoteCLIENTID>/<node>", where node=A,B,C
starterFile="/tmp/remoteUI.txt"

#-------starter functions
def getHwAddr(ifname):
    mac=""
    if(not ifname == ""):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
            mac= ':'.join('%02x' % b for b in info[18:24])
        except socket.error as err:
            mac=""
            print("getHwAddr(): Error: could not get MAC address, using random string")
            print("error=="+str(err)+"==")
    if(ifname == ""):
        length=12
        mac = ''.join(random.choice(string.ascii_uppercase+string.ascii_lowercase+string.digits) for _ in range(length))
    return mac

def getInterface():
    iface=""
    try:
        p = subprocess.Popen(["/sbin/ip", "link", "show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sout, err = p.communicate()
        sout=str(sout,'utf-8')
        for line in sout.split("\n"):
           if(len(line)>0):
               if(not line[0].isspace()):
                   if( ',UP,' in line):
                       if(not ': lo' in line):
                           iface=line.split(":")[1]
                           iface.strip()
    except:
        iface=""
    iface=iface.strip()
    return iface

def getIP():
    ip=""
    #Get IP ADDRESS of this node:
    # from: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((broker_address, 1))
        ip = s.getsockname()[0]
    except socket.error as err:
        ip = '127.0.0.1'
        print("error=="+str(err)+"==")
    finally:
        s.close()
    return str(ip)

#---------Regular Functions
def logitM(msg):
    #
    try:
        fdmw=open(logMFile, 'a')
        fdmw.write(ts()+" -- "+str(msg)+"\n")
        fdmw.close()
    except IOError as e:
        print(ts()+" -- Loging Error found:({})".format(e))
        print("Error: the input file \'"+logMFile+"\' does not exist, see -h for help,  ... exiting ...")
    return

def logit(msg):
    global ql
    if(not len(msg)==0):
        #print("DEBUG: msg =="+msg+"==")
        with trl:
            ql.append(msg)
    return

def logitnow(a,b):
    global ql
    global running
    try:
        fdw=open(logFile, 'a')
        fdw.write(ts()+" --start logitnow()--  \n")
        fdw.flush()
        fdw.close()
    except IOError as e:
        print(ts()+" -- Loging Error found:({})".format(e))
        print("Error: the input file \'"+logFile+"\' does not exist, see -h for help,  ... exiting ...")
    while(running):
        msg=""
        with trl:
            if(not len(ql)==0):
                msg=ql.pop(0)  #pop the first item -- FIFO
        if(not len(msg)==0):
            try:
                fdw=open(logFile, 'a')
                fdw.write(ts()+" -- "+str(msg)+"\n")
                fdw.close()
            except IOError as e:
                print(ts()+" -- Loging Error found:({})".format(e))
                print("Error: the input file \'"+logFile+"\' does not exist, see -h for help,  ... exiting ...")
        else:
            time.sleep(0.2)   #allow CPU time off, nothing to write
    return

def ts():
    return "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())

#def wait4True(globalBool, timeout=50):
#    global globalBool
#    cnt=0
#    error=False
#    while(not globalBool):
#        time.sleep(0.1)
#        cnt=cnt+1
#        if(cnt>timeout):
#            error=True
#            break
#    if(globalBool):
#        error=False
#    return error

def wait4False(globalBool, timeout=50):
    cnt=0
    error=False
    while (globalBool):
        time.sleep(0.1)
        cnt=cnt+1
        if(cnt>timeout):
            error=True
            break
    return error

def doTable(a,b):
    global qm
    global running
    try:
        fdw=open(logFile, 'a')
        fdw.write(ts()+" --start doTable()--  \n")
        fdw.flush()
        fdw.close()
    except IOError as e:
        print(ts()+" -- Loging Error found:({})".format(e))
        print("Error: the input file \'"+logFile+"\' does not exist, see -h for help,  ... exiting ...")
    time.sleep(0.2)
    logit("doTable(): ---start---")
    while(running):
        msg=""
        #with trl:
        if(not len(qm)==0):
            #logit("DEBUG: doTable(): received message")
            msg=qm.pop(0)    #pop first item -- FIFO
            #logit("DEBUG: doTable(): received message: "+str(msg))
        if(not len(msg)==0):
            table(msg.split(';')[0], msg.split(';')[1])   #payload=<command>,<FanRecordedTime>
            #from on_message: table(message.topic+","+payload, ts())   #payload=<command>,<FanRecordedTime>
        else:
            time.sleep(0.2)  #give CPU a break
    return

#----------------------
#table(data) --> puts data into database
#database of Nodes
# FORMAT:
#  <node>=<temp>=<Subtime>=<cmd>=<Subtime>
#  9=17321=2019-02-08 14:53:43=-1=2019-02-08 14:54:55
# PRESENTED AS:
#  Fan Node  Temp        TempRecSubscribeTIme  Command    FanRecordedTime  CmdRecSubscribedTime
#  9         17231       <time>                -1         <time>           <time>
#database of remotes
# FORMAT:
# UInode=command=CtrlNode=lastTimePublished
# PRESENTED AS:
# UINode  command CtrlNode  CmdSubscribe/PubTime
# A       -2      9         <time>
#---------------
# incomming from on_message: data==message.topic+","+payload
def table(data,tsv):    #separate thread to keep the DB updated  #THREADED data=<topic>:<payload>, ts=timestamp
    global nodeDB
    global uiDB
    with trl:
        #do LOCKED threaded action here 
        logit("table(): -------------------entry-------------")
        logit("table(): nodeDB=="+str(nodeDB)+"==, uiDB=="+str(uiDB)+"==eol")
        logit("table(): incoming data=="+str(data)+"==, ts=="+str(tsv)+"==eol")
        (nodeDB, uiDB)=updateDBs(data,tsv,nodeDB,uiDB)  #access the locked variables
        logit("table(): nodeDB=="+str(nodeDB)+"==, uiDB=="+str(uiDB)+"==eol")
        logit("table(): -------------------exit-------------")
    return

def isInt(x):
    truth=False
    try:
        int(x)
        truth=True
    except:
        truth=False
    return truth

def updateDBs(data,ts,nodeDB,uiDB):   
    #from on_message: data==message.topic+","+payload
    sdata=str(data)
    logit("updateDBs: data=="+str(data)+"==, ts=="+str(ts)+"==eol")

    topic=""
    payload=""
    recordedSetTime=""
    fanPayload=""
    isValidPkt=False
    #data='<topic>,<command>,<fanRecordedTime>' ; we split on ',' to access the fields
    if(data.count(',')==2):  #if data count is not 2, then the packet may be a server init packet
        topic=data.split(",")[0].strip()
        payload=data.split(",")[1].strip()
        recordedSetTime=data.split(",")[2].strip()
        logit("updateDBs: topic=="+topic+"==, payload=="+payload+"==, ts=="+ts+"==, recordedTime=="+recordedSetTime+"==")
        fanPayload=data.split(",")[1]+","+data.split(",")[2]
        isValidPkt=True
    #else this packet is not data, but an init garbage packet
    else:
        logit("Error: wrong number of fields in data from on_message, init packet?, data=="+data+"== , isValidPkt=False")
        isValidPkt=False
    tf=topic.split("/")    #tf==creates a list of topic fields, split on '/', the fields are based on below topics
    #topics:
    #temp="nodes/temp/<int(node)>"      
    #cmd="nodes/command/<int(node)>"   
    #rui="rUI/command/<int(node)>/remoteUI-<IP>"

    #decode topics

    #this is looking for integer CtrlNodes -- a CtrlNode reported temp received
    #if(re.match("^"+Topic.temp+"\d",topic)): #not used now, re.match is inefficient 
    #temp topic="nodes/temp/<int(node)>" OR topic="nodes/command/<int(node)>" <==Must have 3 fields
    if(len(tf)==3 and isValidPkt):
        #from on_message: data==message.topic+","+payload
        #temp for message.topic="nodes/temp/<int(node)>"      
        #payload=="<temp>_<lrange>_<hrange>"
        if(tf[0]=="nodes" and tf[1]=="temp" and isInt(tf[2]) and payload.count("_")==2):  #format: nodes/temp/<node#>
            isNew=True
            tmpNodeDB=[]
            ctrlnode=tf[2]  # node#
            temps=payload.strip() #in case temp node client designers add a space before or after temp, we will strip the space out.
            tempsf=temps.split("_")
            for line in nodeDB:
                #modify this line for temp,      ndb[0] ndb[1] ndb[2]   ndb[3]   ndb[4]   ndb[5] ndb[6]    ndb[7]
                #                           ndb=<node>=<temp>=<lrange>=<hrange>=<Subtime>=<cmd>=<Subtime>=<FanRecordedTime>
                #if inNode==node from pos0, then update node with new temp
                if(ctrlnode==line.split("=")[0]):
                    ndb=line.split("=")
                    ndb[1]=tempsf[0] #temp
                    ndb[2]=tempsf[1] #lrange
                    ndb[3]=tempsf[2] #hrange
                    ndb[4]=ts
                    tmpNodeDB.append("=".join(ndb))
                    isNew=False
                    logit("DEBUG: table(): tmpNodeDB="+str(tmpNodeDB))
                else:
                    tmpNodeDB.append(line)
                    logit("DEBUG: table(): tmpNodeDB="+str(tmpNodeDB))
            if(isNew):
                #ndb=<node#>+"="+temp+"="+lrange+"="+hrange+"="+ts+"==="
                ndb=ctrlnode+"="+tempsf[0]+"="+tempsf[1]+"="+tempsf[2]+"="+ts+"==="
                #OLD: ndb=ctrlnode+"="+temp+"="+ts+"==="
                tmpNodeDB.append(ndb)
            nodeDB=tmpNodeDB
        #this is looking for integer CtrlNodes -- a CtrlNode reported a command received 
        #cmd topic="nodes/command/<int(node)>"   
        #After user sets command, and after it reaches the node, the node sends back the command to show it received the command
        elif(tf[0]=="nodes" and tf[1]=="command" and isInt(tf[2])):   # format: node/command/<node#>
            isNew=True
            tmpNodeDB=[]
            cmd=payload.strip()    #XXX
            fanRecordedTime=recordedSetTime
            ctrlnode=tf[2]
            for line in nodeDB:
                #modify this line for temp,      ndb[0] ndb[1] ndb[2]   ndb[3]   ndb[4]   ndb[5] ndb[6]    ndb[7]
                #                           ndb=<node>=<temp>=<lrange>=<hrange>=<Subtime>=<cmd>=<Subtime>=<FanRecordedTime>
                #dbctrlnode=line.split("=")[0]
                #if(ctrlnode==dbctrlnode):
                if(ctrlnode==line.split("=")[0]):  #this is our node, update node with new values
                    ndb=line.split("=")
                    ndb[5]=cmd
                    ndb[6]=ts    #is the time we see it here
                    ndb[7]=fanRecordedTime  #is the time the fan received it
                    tmpNodeDB.append("=".join(ndb))
                    isNew=False
                else:  #this is not our node
                    tmpNodeDB.append(line)
            if(isNew):
                ndb=ctrlnode+"====="+cmd+"="+ts+"="+fanRecordedTime
                tmpNodeDB.append(ndb)
            nodeDB=tmpNodeDB
        else:
            #error message
            logit("Error: topic must be 'nodes/temp' and payload is <temp>_<lrange>_<hrange>, or 'nodes/command', payload is <command> , topic=="+topic+"== , data=="+data+"== , isValidPkt=False")
            isValidPkt=False
    #this is looking for A-Z UINodes -- A UINode gave a command to a node 
    #rui topic="rUI/command/<int(node)>/remoteUI-<IP>" <==Must have 4 fields
    elif(len(tf)==4 and isValidPkt):
        # Problem: On AWS we used the IP & MAC as a differentiator for rUI's, but really a MAC is a random string on PI's that changes 
        #   each start up, so we get many OLD rUI designations, we should only use the latest topic for 'rUI/command/' per rUI
        # 1) would it be better to create a random string and store it in /tmp/<something.rui> file and upon start up check if the file
        #    exists, if so use the random string, if not create one and use it -- random string ???
        #    A) use ip-mac, B) use random numbers, C) use IP-<boxNumber>, D) use NPS login -- so users can ID who is on line for sect2 of demo
        #rui topic="rUI/command/<int(node)>/remoteUI-<IP>"
        if(tf[0]=="rUI" and tf[1]=="command" and isInt(tf[2]) and tf[3].split("-")[0]=="remoteUI"):
            isNew=True
            cmd=payload
            tmpNodeDB=[]
            uiRecordedSetTime=recordedSetTime
            uinode=tf[3]
            #ctrlnode=re.match("^"+Topic.rui+"(\d+)/[A-Z]", topic).group(1) #not used now, re.match is inefficient 
            ctrlnode=tf[2]
            for line in uiDB:
                dbctrlnode=line.split("=")[0]
                if(ctrlnode==dbctrlnode):
                    #modify this line for temp      udb[0]   udb[1]  udb[2] udb[3]            udb[4]
                    #                          udb==CtrlNode=command=UInode=lastTimePublished=recordedTime
                    udb=line.split("=")
                    udb[0]=ctrlnode
                    udb[1]=cmd
                    udb[2]=uinode
                    udb[3]=ts
                    udb[4]=uiRecordedSetTime
                    tmpNodeDB.append("=".join(udb))
                    isNew=False
                else:
                    tmpNodeDB.append(line)
            if(isNew):
                #OLD udb=uinode+"="+cmd+"="+ctrnode+"="+ts
                udb=ctrlnode+"="+cmd+"="+uinode+"="+ts+"="+uiRecordedSetTime
                tmpNodeDB.append(udb)
            uiDB=tmpNodeDB
    else:
        logit("ERROR updateDBs: not a recognized topic, or payload: topic=="+str(topic)+"==, fan payload=="+str(fanPayload)+"==")
        msg="official topics: temp=nodes/temp/<int(node)>, or cmd=nodes/command/<int(node)>, or rui=rUI/command/<int(node)>/remoteUI-<IP>"
        logit(msg)
        msg="official commands=<command:{'','-1','-2','<setpoint>'}>, <fanRecordedTIme>"
        logit(msg)
        logit("")
    return (nodeDB, uiDB)

def getRecentCheckedInNodesFromDB(): #separate thread; called by==> makeChoice(), called by mainUI(), called by main() thread
    global nodeDB
    global uiDB
    with trl:
        #do LOCKED threaded action here 
        recentNodes=[]
        for line in nodeDB:
            node=line.split("=")[0]
            recentNodes.append(node)
    return recentNodes

def displayDBs(CLIENTID): #separate thread; called by==> mainUI(), called by main() thread
    global nodeDB
    global uiDB
    #Problem: finding the latest rUI that gave a command to a node
    #    Should we sort the commands by time?
    with trl:
        #print("nodeDB="+str(nodeDB)+"==")
        print("---------------------Displaying Database--------------")
        #print("From CLIENTID="+str(CLIENTID)+" -- Displaying Database\n")
        print("\nCurrent Control Nodes and state:")
        #do LOCKED threaded action here 
        # uiDB, nodeDB
        s3="   "
        t="\t"
        #print('%10s' % 'node'+s3+'%8s' % 'Temp'+s3+'%20s' % 'Accessed Time'+s3+'%10s' % 'Command'+ s3+'%20s' % 'Data Accessed Time'+'%24s' % 'Fan Recorded Set Time')
        #print(t+"node"+t+"Temp"+t+"Confirmed Time"+t+t+"Command"+t+t+"Last Confirmed Time"+t+"MQTT Server Sent Time")
        print(t+"node"+t+"Temp"+t+"LRange"+t+"HRange"+t+"Confirmed Time"+t+t+"Command"+t+t+"Last Confirmed Time"+t+"MQTT Server Sent Time")
        if(not len(nodeDB)==0):
            for nline in nodeDB:
                ndb=nline.split("=")
                node=str(ndb[0])    #node
                temp=str(ndb[1])    #temp
                lrange=str(ndb[2]) #low range
                hrange=str(ndb[3]) #high range
                tts=str(ndb[4])    #temp time stamp
                cmd=str(ndb[5])    #command
                #OLD: tts=str(ndb[2])  #temp time stamp
                #OLD: cmd=str(ndb[3])  #command
                #commXhrl = { '':"No Command", '-1':"FAN OFF", '-2':"FAN ON" }
                if str(cmd) in commXhrl.keys():
                    cmd = commXhrl.get(str(cmd))
                cts=str(ndb[6]) #command time stamp
                frt=str(ndb[7]) #fan recorded time
                #print('%10s' % n+"   "+'%8s' % t+"   "+'%20s' % tts+"   "+'%10s' % c+"   "+ '%20s' % cts +'%24s' % frt)
                #OLD: print(t+node+t+temp+t+tts+t+"{0:<10s}".format(str(cmd))+t+cts+t+frt)
                print(t+node+t+temp+t+lrange+t+hrange+t+tts+t+"{0:<10s}".format(str(cmd))+t+cts+t+frt)
        else:
            print("\nnothing to display yet\n\n")
        print("\nCurrent UI Nodes and state:")
        #UIDB 
        #print('%10s' % 'UInode'+s3+'%10s' % 'UI Command'+s3+'%10s' % 'Ctrl Node'+ s3+'%20s' % 'Data Accessed Time'+'%24s' % 'Recorded Set Time')
        print(t+"{0:<39s}".format("UInode")+"UI Command"+t+"Ctrl Node"+t+"Last Confirmed Time"+t+"Recorded Set Time")
        if(not len(uiDB)==0):
            for line in uiDB:
                udb=line.split("=")
                cn=udb[0] #ctrl Node
                cmd=udb[1]  #command
                if str(cmd) in commXhrl.keys():
                    cmd = commXhrl.get(str(cmd))    #human readable label
                rn=udb[2] #uiNode
                ts=udb[3] #time stamp
                rt=udb[4] #recorded time
                #print('%10s' % rn+s3+'%10s' % c+s3+'%10s' % cn+s3+'%20s' % ts+'%24s' % rt)
                print(t+"{0:<39s}".format(str(rn))+"{0:<10s}".format(str(cmd))+t+cn+t+t+ts+t+rt)    #XXX
        else:
            print("\nnothing to display yet\n\n")
    return

#----------------------   list=getRecentCheckedInNodesFromDB()
def strList(aList):
    nodes=""
    isFirstItem=True
    for item in aList:
        if(isFirstItem):
            nodes=nodes+item
            isFirstItem=False
        else:
            nodes=nodes+", "+item
    return nodes

def makeChoice(choice):
    node=""
    cmd=""
    if(choice==2 or choice==3 or choice==4 or choice== 5):   #GET NODE
        isOK=BAD
        if str(choice) in commXlater.keys():
            cmd = commXlater.get(str(choice))
        while (isOK):
            nodes=strList(availableNodes)
            lnodes=getRecentCheckedInNodesFromDB()
            snodes=strList(lnodes)
            print("choose node from available nodes: {"+nodes+"}")
            print("choose node from recently checked in nodes: {"+snodes+"}")
            print("or choose 0 to abort")
            try:
                if(sys.version_info >= (3,0)):
                    node = str(input("please choose node: "))     #python3
                else:
                    node = str(raw_input("please choose node: ")) #python2
                if(str(node)=="0"):
                    choice=0
                    isOK=GOOD
                elif str(node) in availableNodes:
                    isOK=GOOD
                else:
                    isOK=BAD
            except:
                isOK=BAD
    else:
        print("Your choise was 6 -- to exit the UI application")
        isOK=BAD
        while (isOK):
            if(sys.version_info >= (3,0)):
                cmd = str(input("Confirm to exit this applicaiton (y/n): "))     #python3
            else:
                cmd = str(raw_input("Confirm to exit this applicaiton (y/n): ")) #python2
            if(not cmd=='y' or cmd=='n'):
                isOK=BAD
                print("Please choose y for yes exit, and n for no do not exit, please try again")
            else:
                isOK=GOOD
        if(cmd=="y"):
            cmd=6
            print("exiting the UI application...")
        else:
            cmd=1
            print("resuming the UI application")
    #set temperature   #XXX
    if choice==5:  
        isOK=BAD
        lowrange=-1
        highrange=-1
        (lowrange, highrange, error) = getLHRanges(node)
        sp=0
        if(error):   #if we do not have a lowrange or a highrange
            while (isOK):
                try:
                    if(sys.version_info >= (3,0)):
                        sp = int(input("choose setpoint: "))     #python3
                    else:
                        sp = int(raw_input("choose setpoint: ")) #python2
                    isOK=GOOD
                except:
                    print("not an integer, or not a number, choose setpoint again")
        else:   #if we have a lowrange or a highrange
            while (isOK and not (sp > lowrange and sp < highrange)):
                try:
                    if(sys.version_info >= (3,0)):
                        sp = int(input("choose setpoint between "+str(lowrange)+" and "+str(highrange)+": "))     #python3
                    else:
                        sp = int(raw_input("choose setpoint between "+str(lowrange)+" and "+str(highrange)+": ")) #python2
                    isOK=GOOD
                except:
                    print("not an integer, or not a number, choose setpoint again")
        cmd=sp
    return (cmd, node, choice)

def getLHRanges(node):
    global nodeDB  #needed to get the controllable lowrange and highrange of the node
    lowrange=-1
    highrange=-1
    error1=True
    error2=True
    error=True
    with trl:      #lock DB and get variable
        nodeDBnow=nodeDB
    for line in nodeDBnow:
        ndb=line.split("=")
        if(ndb[0]==node):
            if(isInt(ndb[2])):
                lowrange=int(ndb[2])
                error1=False
            if(isInt(ndb[3])):
                highrange=int(ndb[3])
                error2=False
            if(not error1 and not error2):
                error=False
    return (lowrange, highrange, error)

def mainUI(CLIENTID):
    runmenu=True
    while runmenu:
        isOK=BAD
        choice=""
        msgMainUI="\n\n\nServer Client "+str(CLIENTID)+" user mode\n\n"
        msgMainUI=msgMainUI+"Command:\n"
        msgMainUI=msgMainUI+"1) view nodes, temps, and commands\n"
        msgMainUI=msgMainUI+"2) set a node to no command\n"
        msgMainUI=msgMainUI+"3) turn a node fan off\n"
        msgMainUI=msgMainUI+"4) turn a node fan on\n"
        msgMainUI=msgMainUI+"5) set the temperature for a node\n"
        msgMainUI=msgMainUI+"6) quit\n"
        msgMainUI=msgMainUI+"Choose command, or '0' to cancel: "
        availableChoices = ['1', '2', '3', '4', '5', '6']
        while (isOK):
            try:
                print(msgMainUI)
                if(sys.version_info >= (3,0)):
                    choice = int(input("please choose 1-6: "))     #python3
                else:
                    choice = int(raw_input("please choose 1-6: ")) #python2
                if str(choice) in availableChoices:
                    isOK=GOOD
                else:
                    isOK=BAD
                    print("\n\nPlease choose from the menu below\n")
                    continue
            except:
                isOK=BAD
        if(choice==1):
            displayDBs(CLIENTID)
            continue
        else:
            (cmd, node, choice) = makeChoice(choice)
        if(choice==2 or choice==3 or choice==4 or choice==5 or choice==6):
           runmenu=False 
    return (cmd, node)

#----------------------
# functions for MQTT
#----------------------
def on_connect(client, userdata, flags, rc):
    global connected
    msg="on connect userdata="+str(userdata)+", flags="+str(flags)+", rc="+str(rc)
    #print(msg)
    logit(msg)
    if(rc==0):
        connected = True
        (error, mID) = client.subscribe(subscribeList)   #SUBSCRIBE HERE
        if(not error==0):
            MQTT_error = " -- not discernible"
            if str(error) in mqtterr.keys():
                MQTT_error = mqtterr.get(str(error))
            msg="client.subscribe error, error="+str(error)+", MQTT_ERROR="+MQTT_error
            print(msg)
            logit("startup on_connect: "+msg)
        else:
            msg="Startup on_connect: no errors"
            logit(msg)
    else:
        msg="connection error"
        print(msg)
        logit(msg)
    return

def on_message(client, userdata, message):   #separate thread -- on_message created by mqtt.Client(CLIENTID); and client.on_message = on_message
    global qm #my queued messages from on_message()
    time.sleep(0.1)
    payload=""
    if(sys.version_info >= (3,0)):
        payload=message.payload.decode()
        #payload=message.payload.decode('ascii')
        #payload=message.payload.decode('UTF-8')
    else:
        payload=message.payload
    #with trl:
    logitM(message.topic+","+payload+';'+ts())
    qm.append(message.topic+","+payload+';'+ts())
    #table(message.topic+","+payload, ts())   #payload=<command>,<FanRecordedTime>
    return

def on_subscribe(client, userdata, mid, granted_qos):
    msg="on subscribe: userdata="+str(userdata)+", mid="+str(mid)+", granted_qos="+str(granted_qos)
    #print(msg)
    logit(msg)
    return

def on_publish(client,userdata,result):             #create function for callback
    #msg=("DEBUG: on_publish(): client=="+str(client)+"==, userdata=="+str(userdata)+"==, result=="+str(result)+"==eol")
    #logit(msg)
    a=0
    return

#----------------------
def wait4True(connected):
    cnt=0
    while(not connected):
        time.sleep(0.1)
        if(cnt>20):
            break
        cnt=cnt+1
    return

def main(client, empty, CLIENTID):      #THREADED
    global connected
    global running
    NODE=CLIENTID
    cnt=0
    print("status: waiting to connect")
    while(not connected):  #initial loop to connect
        print("status: waiting to connect count="+str(cnt))
        wait4True(connected)
        cnt=cnt+1
        if(cnt>12): #wait for 1min, then terminate
            print("not connecting... exiting")
            time.sleep(1)
            running=False
            break
    time.sleep(4)
    print("status: connected")
    running=True
    while(running):   #loop to process 
        time.sleep(0.1)
        (cmd,node) = mainUI(CLIENTID)
        if(cmd==6):
            running=False
            continue
        elif(cmd==1):
            continue
        else: 
            #client.publish(cntopic+str(node), str(cmd))
            msg="main: from:"+CLIENTID+" -- User input -- topic:"+Topic.rui+str(node)+BAR+NODE+", command: "+str(cmd)  #XXX
            logit(msg)
            (error,msgID)= client.publish(Topic.rui+str(node)+BAR+NODE, str(cmd)+","+ts(), qos=2, retain=True)   #PUBLISH HERE
            if(not error==0):
                MQTT_error = " -- not discernible"
                if str(error) in mqtterr.keys():
                    MQTT_error = mqtterr.get(str(error))
                #msg="DEBUG: error="+str(error)+" MQTT ERROR="+MQTT_error+", msgID="+str(msgID)
                #print(msg)
                logit(msg)
    msg="\n\n...exit -- disconnecting from server..."
    print(msg)
    logit(msg)
    client.disconnect()  # to disconnect from server
    msg="\n\n...exiting..."
    print(msg)
    logit(msg)
    os._exit(0)
    return

def runStartMenu(ipAddr, macID, remote_server):        #XXX
    server_address=""
    nodeID=""
    lserv=[]
    eserv=[]
    if(os.path.isfile(starterFile)):
        #file there, use data
        fd=open(starterFile, 'r')
        lines = fd.readlines()
        for l in lines:
            tf=l.split("=")
            if( tf[0] == "node"):
                nodeID=tf[1].rstrip()
                choice = input("previous NodeID found, do you want to use that one, NODE="+nodeID+" (y/n [default=y]): ")
                if(choice == "n" or choice == "N"):
                    nodeID=input("what is your NPS user login (login@nps.edu) [default=remoteUI-IPAddr-macID]: ")
                    if(nodeID == ""):
                        nodeID="remoteUI-"+IPAddr+"-"+macID
                    else:
                        nodeID="remoteUI-"+nodeID
            elif( tf[0] == "local_server"):
                lserv = tf[1].rstrip().split(",")
            elif( tf[0] == "external_server"):
                eserv = tf[1].rstrip().split(",")
        fd.close()
    else:
        #ask user about User Name, login will aid in completing part 2 of the lab
        nodeID=input("what is your NPS user login (login@nps.edu) [default=remoteUI-IPAddr-macID]: ")
        if(nodeID == ""):
            nodeID="remoteUI-"+IPAddr+"-"+macID
        else:
            nodeID="remoteUI-"+nodeID
    #ask user about server
    result=input("Do you want to use a server on your local network (y,n [default=y])? ")
    if(not result == "n" and not result == "N"):
        local="localhost"
        cnt=0
        lcnt=0
        ask=True
        ichoice=""
        while(ask):
            choice=""
            print("What server would you like to use:")
            for serv in lserv:
                if(not len(serv) == 0):
                    print(str(cnt)+") "+serv)
                    cnt=cnt+1
            print(str(cnt)+") localhost")
            lcnt=cnt
            cnt=cnt+1
            print(str(cnt)+") specify a new server")
            choice = input("Choose a number from above [default=localhost]: ")
            if(choice == ""):
                server_address=local
                ask=False
                ichoice=lcnt
            elif(isInt(choice)):
                ichoice=int(choice)
                ask=False
            else:
                ask=True
                print("please choose only the numbers shown, please retry.")
        if(ichoice < cnt):
            if( ichoice == (cnt - 1)):
                server_address=local
            else:
                server_address=lserv[ichoice]
        elif(ichoice == cnt):
            sip=input("input the Servers IP on the local network where your server is running: ")
            lserv.append(sip)
            server_address=sip
    #use remote_server
    else:
        ask=True
        ichoice=""
        while(ask):
            cnt=0
            choice=""
            print("What server would you like to use:")
            for serv in eserv:
                if(not len(serv) == 0):
                    print(str(cnt)+") "+serv)
                    cnt=cnt+1
            print(str(cnt)+") "+remote_server+" [default]")
            lcnt=cnt
            cnt=cnt+1
            print(str(cnt)+") specify a new server")
            choice = input("Choose a number from above (note the default server): ")
            if(choice == ""):
                server_address=remote_server
                ask=False
                ichoice=lcnt
            elif(isInt(choice)):
                ichoice=int(choice)
                ask=False
            else:
                ask=True
                print("please choose only the numbers shown, please retry.")
        if(ichoice < cnt):
            if( ichoice == (cnt - 1)):
                server_address=remote_server
            else:
                server_address=eserv[cnt]
        elif(ichoice == cnt):
            sip=input("input your remote Server DNS listing or IP where your server is running: ")
            eserv.append(sip)
            server_address=sip
    #write out file    
    fd=open(starterFile, 'w')
    fd.write("node="+str(nodeID)+"\n")
    fd.write("local_server="+','.join(lserv)+"\n")
    fd.write("external_server="+','.join(eserv)+"\n")
    fd.close()
    return (nodeID, server_address)

def cleanup():
    global running
    running=False
    return

def start():
    global running
    running=True
    return

#-----------main start
if __name__ == "__main__":
    logit("starting remote MQTT client .... "+str(sys.argv[0]))
    start()
    mac = getHwAddr(getInterface())
    IPAddr=getIP()
    print("At start: IPADDR=="+str(IPAddr))
    print("mac address = "+str(mac))
    macID=mac.replace(":", "")

    (NODE, broker_address) = runStartMenu(IPAddr, macID, remote_server)
    print("MQTT Server Address: "+str(broker_address))

    print("node="+NODE)
    CLIENTID=NODE
    subscribeList=[]
    subscribeList.append((Topic.temp+ANY, qos))  #the '#' mark is a wild card for topics
    subscribeList.append((Topic.cmd+ANY, qos))
    subscribeList.append((Topic.rui+ANY, qos))

    print("starting...")
    logit("\n\nstarting ...")
    client=mqtt.Client(CLIENTID)               #create client object
    client.on_publish = on_publish
    client.on_connect = on_connect
    client.on_message = on_message    # allows access to messages sent to MQTT Broker/Server designates function name as: on_message()
    client.on_subscribe = on_subscribe
    logt=threading.Thread(target = logitnow, args =  (empty, empty2))
    tablet=threading.Thread(target = doTable, args =  (empty, empty2))
    maint=threading.Thread(target = main, args =  (client, empty2, NODE))
    try:
        logt.start()
        time.sleep(0.2)
        tablet.start()
        time.sleep(0.2)
        client.connect(host=broker_address, port=mqttport, keepalive=60) #establish connection
        time.sleep(0.2)
        client.loop_start()
        time.sleep(0.2)
        maint.start()
        #client.loop_forever()
    except KeyboardInterrupt:
        cleanup()
        time.sleep(0.5)
        print("\n\nUser Key Board Interrupt ...exiting...")
        #client.disconnect()  # to disconnect from server   --- goes with client.loop_forever()
        client.loop_stop()  # MQTT-Paho thread terminated   --- goes with  client.loop_start()
        #tablet.join()       # tablet thread terminated
        #maint.join()        # maint thread terminated
        os._exit(0)
    except Exception as e:
        print("Error: exception occured -- error was: "+str(e))
        os._exit(1)
#cleaner way to terminate all threads below
main_thread = threading.currentThread()
for t in threading.enumerate():
    if t is not main_thread:
        t.join()
os._exit(0)

