import paho.mqtt.client as mqtt
import json
import sqlite3
# MQTT broker details
MQTT_BROKER = "192.168.178.164"  # Replace with your Raspberry Pi IP
MQTT_PORT = 1883
MQTT_USERNAME = "dimash"  # Replace with your MQTT username
MQTT_PASSWORD = "dimash"  # Replace with your MQTT password
SENSOR_TOPIC = "sensor"
# Replace with your sensor topic name
dbname='/home/dimash/Sensors_Database/bmeWebServer/sensorsData.db'




def logData (temp, hum, pres):	
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	curs.execute("INSERT INTO BME_data values(datetime('now'), (?), (?), (?))", (temp, hum, pres))
	conn.commit()
	conn.close()
# display database data
def displayData():
	conn=sqlite3.connect(dbname)
	curs=conn.cursor()
	print ("\nEntire database contents:\n")
	for row in curs.execute("SELECT * FROM BME_data"):
		print (row)
	conn.close()

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to the topic
        client.subscribe(SENSOR_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
    print(f"Raw received message: {msg.payload.decode()} on topic: {msg.topic}")
    message = msg.payload.decode()
    print(f"Received message: {message} on topic: {msg.topic}")
#     
#     try:
#         # Try parsing the message into float (if values are numerical)
#         value = float(message)
#         print(f"Parsed value: {value}")
#     except ValueError:
#         print("Received non-numeric value, cannot parse!")
    try:
        # Parse JSON message
        
        sensor_data = json.loads(message)
        temp = float(sensor_data.get("temperature"))
        hum = float(sensor_data.get("humidity"))
        pres = float(sensor_data.get("pressure"))
        
        temp = round(temp, 1)
        hum = round(hum)
        pres=round(pres)
        
#         print(f"Temperature: {temp} °C")
#         print(f"Humidity: {hum} %")
#         print(f"Pressure: {pres} hPa")
        
        logData (temp, hum, pres)
        displayData()
    except json.JSONDecodeError:
        print("Error: Could not decode JSON message")

# Create MQTT client
client = mqtt.Client()

# Set username and password for the MQTT broker
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
try:
    print("Connecting to MQTT broker...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
    print(f"Error connecting to MQTT broker: {e}")
    exit(1)

# Start the MQTT client loop to listen for messages
print("Listening for messages...")
client.loop_forever()

