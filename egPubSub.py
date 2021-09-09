#!/usr/bin/python3
# Adapted from example code published in
#    http://www.steves-internet-guide.com/into-mqtt-python-client/
#
import paho.mqtt.client as mqtt #import the client1
import time
############
def on_message(client, userdata, message):
    print("on_message(): payload="+str(message.payload.decode()))
    print("on_message(): topic=",message.topic)
    print("on_message(): qos=",message.qos)
    print("on_message(): retain flag=",message.retain)
########################################
broker_address="127.0.0.1"

topic="home/lights/livingRoom"

#subscribe
print("creating new subscriber S1")
client1 = mqtt.Client("S1") #create new subscriber instance called "S1"
client1.on_message=on_message #attach function to callback
print("S1 connecting to broker")
client1.connect(broker_address) #connect to broker
print("S1 subscribing to topic",topic, "\n")
client1.subscribe(topic)
client1.loop_start() #start the loop, because subscribe must receive the callback

#publish
print("creating new publisher Pt \n")
client2 = mqtt.Client("Pt") #create new publisher instance called "P1"
print("Pt connecting to broker")
client2.connect(broker_address) #connect to broker
#publish1
msg1 = "turn-on"
print("publishing Topic=="+topic+"== , message=="+msg1+"==eol" )
client2.publish(topic, msg1)
time.sleep(3) # wait for 3 seconds
#publish2
msg1 = "turn-off"
print("publishing Topic=="+topic+"== , message=="+msg1+"==eol" )
client2.publish(topic, msg1)
#client2.loop_start() #start the loop -- publish does not need to start loop, as there is no callback for it
time.sleep(3) # wait for 3 seconds

#put main() here between try/except for KeyboardInterrupt

client2.loop_stop() #stop the client loop
#client1.disconnect()  -- used with client1.loop_forever() -- reports of glitches with this 
client2.disconnect()  #-- used with client2.loop_forever()
print("\nClients successfully disconnected")

