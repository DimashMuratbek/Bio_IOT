from machine import Pin
from time import sleep

# ESP32 GPIO 26
relay = Pin(25, Pin.OUT)
motor_relay= Pin(26, Pin.OUT)
# ESP8266 GPIO 5
#relay = Pin(5, Pin.OUT)

while True:
  # RELAY ON
  relay.value(0)
  motor_relay.value(0)
  
  print('On')
  sleep(5)
  
  # RELAY OFF
  relay.value(1)
  motor_relay.value(1)
  print('Off')
  sleep(5)