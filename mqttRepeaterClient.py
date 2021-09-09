#!/usr/bin/python3
#!/Library/Frameworks/Python.framework/Versions/3.9/bin/python3   #MACOSX BigSur
#!/usr/local/bin/python
#from: https://os.mbed.com/teams/Cloud-Hackathon/code/MQTT-Python-Demo/file/cc36d40e9bf5/broker/broker.py/
import paho.mqtt.client as mqttbroker
import socket
import sys
# nodename nor servname 
#Your IP address is:
#Traceback (most recent call last):
#File "./mqttbroker.py", line 37, in <module>
#print "Your IP address is:", socket.gethostbyname(socket.gethostname())
#socket.gaierror: [Errno 8] nodename nor servname provided, or not known

# https://os.mbed.com/teams/mqtt/wiki/Using-MQTT#python-client

#logfile
fl="mqtBrokerLog.txt"
fdl=open(fl, "w")

#static msgs
fm="mqtBrokerMsgsHistory.txt"
fdm=open(fm, "w")

  
# MQTT broker hosted on local machine
mqttc = mqttbroker.Client()
   
# Settings for connection
#host = "172.20.145.206"
host="localhost"
host="172.20.105.184"  #SECTION2
host="172.20.109.43"   #SECTION1
host="10.0.0.145"   #Home
broker_address="ec2-54-193-32-216.us-west-1.compute.amazonaws.com" #AWS
host="ec2-54-193-32-216.us-west-1.compute.amazonaws.com" #AWS
host = "localhost"
myport=1883
topic= "#"
    
# Callbacks
def on_connect(self, mosq, obj, rc):
    print("Connected rc: " + str(rc))
             
def on_message(mosq, obj, msg):
    msg="[Received] Topic: " + msg.topic + ", Message: " + str(msg.payload) + "\n"
    #print("[Received] Topic: " + msg.topic + ", Message: " + str(msg.payload) + "\n");
    print(msg)
    #fdm.write(msg)
                      
def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed OK")
                               
def on_unsubscribe(mosq, obj, mid, granted_qos):
    print("Unsubscribed OK")

if __name__ == "__main__":
   print("starting..")
   try:
   # Set callbacks
      mqttc.on_message = on_message
      mqttc.on_connect = on_connect
      mqttc.on_subscribe = on_subscribe
      mqttc.on_unsubscribe = on_unsubscribe

      # Connect and subscribe
      #print "Your IP address is:", socket.gethostbyname(socket.gethostname())
      print("Connecting to " + host + "/" + topic)
      try:
         mqttc.connect(host, port=myport, keepalive=60)
         mqttc.subscribe(topic, 0)
      except Exception as e:
          print("Error: exception -- error was: "+str(e))
          sys.exit(1)

      #print "Your IP address is:", socket.gethostbyname(socket.gethostname())
      # Loop forever, receiving messages
      mqttc.loop_forever()

      print("rc: " + str(rc))

   except KeyboardInterrupt:
      print("\nuser interrupt with CTRL-C, exiting ...")
      sys.exit(0)
   except:
      print("Exiting...")
      sys.exit(1)
