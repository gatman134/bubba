# Program By Daniel batista
# Made for the Adafruit_ADS1x15
# Fan controller for maintaining thermistor temperature

import time
from datetime import datetime
import Adafruit_ADS1x15
import subprocess
import os
import sys
import errno


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

GAIN=1
adc=Adafruit_ADS1x15.ADS1115()

print("To exit the program please use CTRL+C")

while True:
  temp = adc.read_adc(channel=0, gain=GAIN, data_rate=128)
  now = datetime.now();
  today = now.strftime("%Y-%m-%d %H:%M:%S")
  if temp > set_temp:
        ON = os.system("sudo uhubctl -l 2 -a 1")
        print(today,", Setpoint ="+str(set_temp), ", temp ="+str(temp), ", fan =ON")
  if temp < set_temp:
        OFF = os.system("sudo uhubctl -l 2 -a 0")
        print(today,", Setpoint ="+str(set_temp), ", temp ="+str(temp), ", fan =OFF")   
  time.sleep(int(wait_time))