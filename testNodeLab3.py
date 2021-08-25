#!/usr/bin/python3
#!/usr/bin/python
#!/usr/local/bin/python
#
from socket import *
import sys
import time
import os
import datetime


#globals
BAD=True
GOOD=False
clientLogFile="log.eg1Node.txt"
try:
    fdlog=open(clientLogFile, 'a')
except IOError as e:
    print("Error found:({})".format(e))
    print("Error: the input file \'"+clientLogFile+"\' does not exist, see -h for help,  ... exiting ...")
    sys.exit(0)
fdlog.write("Starting Client Node at: "+"{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())+"\n")
fdlog.flush()

#subs
def ts():
    return "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())
def logit(msg):
    fdlog.write(msg+"\n")
    fdlog.flush()
    return
#-------
def rcv(clientsocket):
    responsePkt = clientsocket.recv(1024)
    response = responsePkt.decode('ascii')
    return response
def snd(clientsocket, msg):
    clientsocket.send(msg.encode('ascii'))
    return 
def mainClient():
   isOK=BAD
   limLow=15000
   limHigh=33000
   while isOK:
      try:
         nodeNumber = int(input("Enter Node Number: "))
         temp = input("Enter temp: ")
         isOK=GOOD
      except ValueError:
         print("not a integer")
         isOK=BAD
   print("Node "+str(nodeNumber))
   logit("Node "+str(nodeNumber))
   isOK=BAD
   while isOK:
      try:
         limLow = int(input("Enter Lowest controllable temp: "))
         limHigh = int(input("Enter Highest controllable temp: "))
         isOK=GOOD
      except ValueError:
         print("not a integer")
         isOK=BAD
   print ("Low limit="+str(limLow))
   print ("High limit="+str(limHigh))

   # Set up the socket as an Internet facing streaming socket
   clientsocket = socket(AF_INET, SOCK_STREAM)
   # Connect to the server on port 4000
   try:
      clientsocket.connect(('localhost', 4000))
   #except socket.error:
   except socket:
      print("Error: socket.error")
      sys.exit(0)
   except: 
      print("Error: general connection error")
      sys.exit(0)

   print("connected!")
   # Send the greeting message to the server, as specified by the requirements
   msg = "Node: "+str(nodeNumber)
   #clientsocket.send(message.encode('ascii'))
   snd(clientsocket,msg)

   # Wait for a response, then print said response to the console
   response = rcv(clientsocket)
   print(response)

   msg = "Temp: "+str(temp)+" "+str(limLow)+" "+str(limHigh)
   #clientsocket.send(message.encode('ascii'))
   snd(clientsocket,msg)

   # Wait for a response, then print said response to the console
   response = rcv(clientsocket)
   print(response)

   #initial connection ready, now run continuously
   running = 1
   while running:
       #send temp
       #get command
      
      #Get temp from PI ADC--ADS1115
      # For demo purposes, Ask for user to set the temperature
      temp = int(input("Enter new Temp: "))
      # Format the temp packet, ready to send to the server
      msg = "Temp: " + str(temp) 
      snd(clientsocket,msg)

      # Wait for the response from the server
      #receive command; command packet=="command: <command>" , where command=(-1==FANOFF, -2==FANON, temp==tempSetpoint)
      commandPkt = rcv(clientsocket)
      print ("received from server commandPkt:"+commandPkt)
      if(len(commandPkt.split()) == 1):
          command=""
      else:
          command=commandPkt.split()[1]
      print ("received from server command==>"+command+"<==")
      
      #do something with this command

      #sleep
      time.sleep(1.0)

   clientsocket.close()
   return

if __name__ == "__main__":
   print("starting..")
   try:
      mainClient()
   except KeyboardInterrupt:
      print("\nuser shutdown, ...exiting...")
      os._exit(0)
