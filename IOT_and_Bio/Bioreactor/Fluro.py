from machine import Pin, SoftI2C
from time import sleep
from tsl2591 import Tsl2591  # Ensure tsl2591.py is in the same directory as your main script

# Pin Definitions
POWERLED_RELAY_PIN = Pin(5, Pin.OUT)
INDICATOR_LED_FLUOROMETRY = Pin(2, Pin.OUT)
FLUOROMETRY_SWITCH_LED_PIN = Pin(34, Pin.IN)

# Initialize I2C and Sensor
i2c = SoftI2C(scl=Pin(18), sda=Pin(19))  # Adjust pins as per your setup
tsl = Tsl2591()  # Initialize the TSL2591 sensor

def read_luminosity():
    full, ir = tsl.get_full_luminosity()
    lux = tsl.calculate_lux(full, ir)
    return lux  # Return only the lux value

# Main Program
while True:
    lux_value = read_luminosity()  # Get only the lux value
    print(f"{lux_value:.6f}")  # Print the lux value with six decimal places
    sleep(0.5)
