import paho.mqtt.client as mqtt
import json
import sqlite3
import argparse
import time
from azure.iot.device import IoTHubDeviceClient, Message
from azure.iot.device.exceptions import (
    ConnectionFailedError, ConnectionDroppedError, OperationTimeout, 
    OperationCancelled, NoConnectionError
)
from dotenv import load_dotenv
from log import console, log
import config
load_dotenv()
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import io
import threading
from flask import Flask, render_template,send_file, make_response, request
app = Flask(__name__)
import threading


# MQTT Broker details
MQTT_BROKER = "192.168.178.164"  # Replace with your Raspberry Pi IP
MQTT_PORT = 1883
MQTT_USERNAME = "dimash"  # Replace with your MQTT username
MQTT_PASSWORD = "dimash"  # Replace with your MQTT password
SENSOR_TOPIC = "sensor"  # Replace with your sensor topic name
#dbname = '/home/dimash/Sensors_Database/sensorsData.db'
dbname= '/home/dimash/Sensors_Database/bmeWebServer/sensorsData.db'


# Azure IoT Hub Configuration
parser = argparse.ArgumentParser()
parser.add_argument("connection", nargs='?', help="Device Connection String from Azure", 
                    default=config.IOTHUB_DEVICE_CONNECTION_STRING)
parser.add_argument("-t", "--time", type=int, default=config.MESSAGE_TIMESPAN,
                    help="Time in between messages sent to IoT Hub, in milliseconds (default: 2000ms)")
parser.add_argument("-n", "--no-send", action="store_true", 
                    help="Disable sending data to IoTHub, only print to console")
ARGS = parser.parse_args()







# Function to log data into the database
def logData(temp, hum, pres):
    conn = sqlite3.connect(dbname)
    curs = conn.cursor()
    curs.execute("INSERT INTO BME_data VALUES(datetime('now'), ?, ?, ?, 0)", (temp, hum, pres))
    conn.commit()
    conn.close()


def send_message(device_client: IoTHubDeviceClient, message):
    telemetry = Message(json.dumps(message))
    telemetry.content_encoding = "utf-8"
    telemetry.content_type = "application/json"
    try:
        device_client.send_message(telemetry)
    except (ConnectionFailedError, ConnectionDroppedError, OperationTimeout, OperationCancelled, NoConnectionError):
        log.warning("Message failed to send, skipping")
    else:
        log.success("Message successfully sent!", message)
        
        
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(SENSOR_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")


#Receive message from esp32
def on_message(client, userdata, msg):
#     print(f"Received message: {msg.payload.decode()} on topic: {msg.topic}")
    message = msg.payload.decode()
    print(f"Received message: {message} on topic: {msg.topic}")
    try:
        sensor_data = json.loads(msg.payload.decode())
        temp = float(sensor_data.get("temperature"))
        pH = float(sensor_data.get("humidity"))
        flow = float(sensor_data.get("pressure"))
        
        temp = round(temp, 1)
        hum = round(hum)
        pres=round(pres)

        log_data(temp, hum, pres)
        
        conn = sqlite3.connect('/home/dimash/Sensors_Database/bmeWebServer/sensorsData.db')
        curs = conn.cursor()
    
        curs.execute("SELECT * FROM BME_data ORDER BY timestamp DESC LIMIT 1")
        row = curs.fetchone()
        
        if row:
            # Create message object with sensor data
            message = {
#               "deviceId": "ESP32 - Python",
                "timestamp": row[0],
                "temp": row[1],
                "hum": row[2],
                "pres": row[3]
                }

                # Send SQLite sensor data to Azure IoTHub
            if ARGS.no_send:
                log.warning("Not sending to IoTHub", message)
            else:
                with console.status("Sending message to IoTHub...", spinner="bouncingBar"):
                    send_message(device_client, message)

        # Wait for interval
        time.sleep(ARGS.time / 1000)
    
    except json.JSONDecodeError:
        print("Error: Could not decode JSON message")







def getLastData():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("SELECT * FROM BME_data ORDER BY timestamp DESC LIMIT 1"):
        time = str(row[0])
        temp = row[1]
        hum = row[2]
        pres = row[3]
    #conn.close()
    return time, temp, hum, pres



# Flask route for the main webpage
def getHistData (numSamples):
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    curs.execute("SELECT * FROM BME_data ORDER BY timestamp DESC LIMIT "+str(numSamples))
    data = curs.fetchall()
    time = []
    temp = []
    hum = []
    pres =[]
    for row in reversed(data):
        time.append(row[0])
        temp.append(row[1])
        hum.append(row[2])
        pres.append(row[3])
    return time, temp, hum, pres

def maxRowsTable():
    conn=sqlite3.connect(dbname)
    curs=conn.cursor()
    for row in curs.execute("select COUNT(temp) from  BME_data"):
        maxNumberRows=row[0]
    return maxNumberRows

global numSamples
numSamples = maxRowsTable()
if (numSamples > 101):
    numSamples = 100




###########################################################




@app.route("/")
def index():
    time, temp, hum, pres = getLastData()
    templateData = {
        'time': time,
        'temp': temp,
        'hum': hum,
        'pres': pres,
        'numSamples': numSamples
    }
    return render_template('index.html', **templateData)

@app.route('/', methods=['POST'])
def my_form_post():
    global numSamples 
    numSamples = int (request.form['numSamples'])
    numMaxSamples = maxRowsTable()
    if (numSamples > numMaxSamples):
        numSamples = (numMaxSamples-1)
    
    time, temp, hum, pres = getLastData()
    
    templateData = {
      'time' : time,
      'temp' : temp,
      'hum' : hum,
      'pres': pres,
      'numSamples': numSamples
    }
    return render_template('index.html', **templateData)


@app.route('/plot/temp')
def plot_temp():
    time, temp, hum,pres = getHistData(numSamples)
    ys = temp
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Temperature [°C]")
    axis.set_xlabel("Samples")
    axis.grid(True)
    xs = range(numSamples)
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route('/plot/hum')
def plot_hum():
    time, temp, hum,pres = getHistData(numSamples)
    ys = hum
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Humidity [%]")
    axis.set_xlabel("Samples")
    axis.grid(True)
    xs = range(numSamples)
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response



@app.route('/plot/pres')
def plot_pres():
    time, temp, hums,pres = getHistData(numSamples)
    ys = pres
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("Pressure [mb]")
    axis.set_xlabel("Samples")
    axis.grid(True)
    xs = range(numSamples)
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

# MQTT callback when connected to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(SENSOR_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")





# Main entry point
if __name__ == "__main__":
    # Start the MQTT client in a separate thread
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    
    
    
#     app.run(host='0.0.0.0', port=5000, debug=False)
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
    flask_thread.start()
    # Connect to MQTT broker
    try:
        print("Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        exit(1)
    
 
    
    # Azure IoT Hub Client Setup
    device_client = None
    if not ARGS.no_send:
        try:
            device_client = IoTHubDeviceClient.create_from_connection_string(ARGS.connection)
            device_client.connect()
            log.success("Connected to Azure IoT Hub")
        except Exception as e:
            print(f"Error connecting to Azure IoT Hub: {e}")
            exit(1)

    # Start MQTT loop
    try:
        print("Listening for messages...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if device_client:
            device_client.shutdown()


