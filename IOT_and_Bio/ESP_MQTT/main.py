# Complete project details at https://RandomNerdTutorials.com/micropython-programming-with-esp32-and-esp8266/
from machine import Pin, SoftI2C
from time import sleep
import BME280
import json

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000) #BME280 pins

def sub_cb(topic, msg):
  print((topic, msg))
  if topic == b'notification' and msg == b'received':
    print('ESP received hello message')

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, mqtt_server, user=mqtt_user, password=mqtt_pass)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()

# mosquitto_sub -d -t sensor -u dimash -P dimash





while True:
  #read data from bme280 and assign them to variables
  bme = BME280.BME280(i2c=i2c)
  temperature = bme.temperature
  humidity = bme.humidity
  pressure = bme.pressure


  temp =temperature.replace('C', '')  # Removes "C"
  hum = humidity.replace('%', '')  # Removes "%"
  pres = pressure.replace('hPa', '') #Romeves "hpa"
  
  try:
    client.check_msg()
    if (time.time() - last_message) > message_interval:
        
            
      # put values in message
      sensor_data = {
          "temperature": temp,
          "humidity": hum,
          "pressure": pres
          }
      # publish them to broker
      client.publish(sensor_topic, json.dumps(sensor_data))

      print(temp,' ',hum,' ', pres)
      last_message = time.time()
      counter += 1
  except OSError as e:
    restart_and_reconnect()
