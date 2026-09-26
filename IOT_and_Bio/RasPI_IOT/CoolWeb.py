from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
from flask import Flask, render_template,send_file, make_response, request

import sqlite3
import paho.mqtt.client as mqtt
import json
import threading

app = Flask(__name__)

# MQTT Broker details
MQTT_BROKER = "192.168.178.164"  # Replace with your Raspberry Pi IP
MQTT_PORT = 1883
MQTT_USERNAME = "dimash"  # Replace with your MQTT username
MQTT_PASSWORD = "dimash"  # Replace with your MQTT password
SENSOR_TOPIC = "sensor"  # Replace with your sensor topic name
#dbname = '/home/dimash/Sensors_Database/sensorsData.db'
dbname= '/home/dimash/Sensors_Database/bmeWebServer/sensorsData.db'



# Function to log data into the database
def logData(temp, hum, pres):
    conn = sqlite3.connect(dbname)
    curs = conn.cursor()
    curs.execute("INSERT INTO BME_data VALUES(datetime('now'), ?, ?, ?, 0)", (temp, hum, pres))
    conn.commit()
    conn.close()

# # Retrieve the latest data from the database
# def getData():
#     conn = sqlite3.connect(dbname)
#     curs = conn.cursor()
# 
#     # Initialize default values
#     time, temp, hum, pres = "No Data", "N/A", "N/A", "N/A"
# 
#     # Fetch the latest row
#     row = curs.execute("SELECT * FROM BME_data ORDER BY timestamp DESC LIMIT 1").fetchone()
#     if row:
#         time = str(row[0])
#         temp = row[1]
#         hum = row[2]
#         pres = row[3]
# 
#     conn.close()
#     return time, temp, hum, pres

############################################
#*************************************

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

# MQTT callback when a message is received
def on_message(client, userdata, msg):
    print(f"Raw received message: {msg.payload.decode()} on topic: {msg.topic}")
    try:
        # Parse the JSON message
        sensor_data = json.loads(msg.payload.decode())
        temp = float(sensor_data.get("temperature"))
        hum = float(sensor_data.get("humidity"))
        pres = float(sensor_data.get("pressure"))

        # Round values for consistency
        temp = round(temp, 1)
        hum = round(hum)
        pres = round(pres)

        print(f"Temperature: {temp} °C")
        print(f"Humidity: {hum} %")
        print(f"Pressure: {pres} hPa")

        # Log the data into the database
        logData(temp, hum, pres)

    except json.JSONDecodeError:
        print("Error: Could not decode JSON message")

# Function to start the MQTT client loop in a separate thread
def start_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print("Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

# Main entry point
if __name__ == "__main__":
    # Start the MQTT client in a separate thread
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    # Start the Flask application
    app.run(host='0.0.0.0', port=5000, debug=False)
