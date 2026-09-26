from flask import Flask, render_template, request
app = Flask(__name__)
import sqlite3
# Retrieve data from database
def getData():
    conn=sqlite3.connect('/home/dimash/Sensors_Database/sensorsData.db')
    curs=conn.cursor()
    for row in curs.execute("SELECT * FROM BME_data ORDER BY timestamp DESC LIMIT 1"):
        time = str(row[0])
        temp = row[1]
        hum = row[2]
        pres = row[3]
    conn.close()
    return time, temp, hum, pres


@app.route("/")
def index():
    time, temp, hum, pres = getData()
    templateData = {
        'time': time,
        'temp': temp,
        'hum': hum,
        'pres': pres
        
    }
    return render_template('index.html', **templateData)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=False)
