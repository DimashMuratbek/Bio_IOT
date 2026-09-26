import config
import argparse
import sqlite3
from azure.iot.device import IoTHubDeviceClient
from azure.iot.device import Message
from azure.iot.device.exceptions import ConnectionFailedError, ConnectionDroppedError, OperationTimeout, OperationCancelled, NoConnectionError
from log import console, log
from dotenv import load_dotenv
import time
import json
import argparse

load_dotenv()

# SECTION 1: Argument Parsing
# Parse arguments before anything for faster feedback
parser = argparse.ArgumentParser()
parser.add_argument("connection", nargs='?', help="Device Connection String from Azure", 
                    default=config.IOTHUB_DEVICE_CONNECTION_STRING)
parser.add_argument("-t", "--time", type=int, default=config.MESSAGE_TIMESPAN,
                    help="Time in between messages sent to IoT Hub, in milliseconds (default: 2000ms)")
parser.add_argument("-n", "--no-send", action="store_true", 
                    help="Disable sending data to IoTHub, only print to console")
ARGS = parser.parse_args()
#changed

# SECTION 2: Function to Send Message to IoTHub
# Function to send a message to Azure IoTHub
def send_message(device_client: IoTHubDeviceClient, message):
    telemetry = Message(json.dumps(message))
    telemetry.content_encoding = "utf-8"
    telemetry.content_type = "application/json"
    
    try:
        device_client.send_message(telemetry)
    except (ConnectionFailedError, ConnectionDroppedError, OperationTimeout, OperationCancelled, NoConnectionError):
        log.warning("Message failed to send, skipping")
        return False
    else:
        log.success("Message successfully sent!", message)
        return True

# SECTION 3: Main Function
# Main function to handle connection to IoTHub and send data from SQLite
def main():
    if not ARGS.connection and not ARGS.no_send:  # If no argument
        log.error("IOTHUB_DEVICE_CONNECTION_STRING in config.py variable or argument not found, try supplying one as an argument or setting it in config.py")
    
    device_client = None
    if not ARGS.no_send:
        with console.status("Connecting to IoT Hub with Connection String", spinner="arc", spinner_style="blue"):
            # Create instance of the device client using the connection string
            device_client = IoTHubDeviceClient.create_from_connection_string(ARGS.connection, connection_retry=False)

            # Connect the device client.
            try:
                device_client.connect()
                log.success("Connected to IoT Hub")
            except (ConnectionFailedError, ConnectionDroppedError, NoConnectionError):
                log.error("Failed to connect to IoT Hub")
    
    # Connect to SQLite database
    conn = sqlite3.connect('/home/dimash/Sensors_Database/bmeWebServer/sensorsData.db')
    cursor = conn.cursor()

    # Create a column to track if data has been sent
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS sensor_data (
#         time TEXT PRIMARY KEY,
#         temperature REAL,
#         humidity REAL,
#         pressure REAL,
#         sent BOOLEAN DEFAULT 0
#     )
#     """)
#     conn.commit()

    try:
        while True:
            # Retrieve data that has not been sent
            cursor.execute("SELECT timestamp, temp, hum, pres FROM BME_data WHERE sent = 0 ORDER BY timestamp ASC")
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    # Create message object with sensor data
                    message = {
#                         "deviceId": "ESP32 - Python",
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
                            if send_message(device_client, message):
                                # Mark the row as sent
                                cursor.execute("UPDATE BME_data SET sent = 1 WHERE timestamp = ?", (row[0],))
                                conn.commit()

            # Wait for interval
            time.sleep(ARGS.time / 1000)
    except KeyboardInterrupt:
        # Shut down the device client when Ctrl+C is pressed
        log.error("Shutting down", exit_after=False)
        if device_client:
            device_client.shutdown()
    finally:
        # Close the SQLite connection
        conn.close()

# SECTION 4: Entry Point
# Entry point for the script
if __name__ == "__main__":
    main()

