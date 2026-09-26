from machine import Pin, PWM
from tsl2591 import Tsl2591  # Assuming tsl2591.py is available
import time

# Pin definitions
POWERLED_RELAY_PIN = 5
FLUOROMETRY_SWITCH_LED_PIN = 34
INDICATOR_LED_FLUOROMETRY = 4

# Constants
SWITCH_DELAY = 0.06  # 60ms in seconds
STATE_NONE = 0
STATE_COLORIMETRY = 1
STATE_COLORIMETRY_FADE = 2
STATE_FLUOROMETRY = 3

# Initialize pins
power_led_relay = Pin(POWERLED_RELAY_PIN, Pin.OUT)
fluorometry_switch = Pin(FLUOROMETRY_SWITCH_LED_PIN, Pin.IN, Pin.PULL_DOWN)
indicator_led_fluorometry = Pin(INDICATOR_LED_FLUOROMETRY, Pin.OUT)

# Initialize sensor
try:
    tsl = Tsl2591('lux-1')  # Pass sensor ID
    print("TSL2591 initialized.")
except Exception as e:
    print(f"Sensor initialization failed: {e}")
    tsl = None

# State variables
state = STATE_NONE
brightness = 0
fade_amount = 5  # Change brightness by 5 units

def display_sensor_details():
    """Display sensor details."""
    print("Sensor details:")
    print(f"Integration time: {tsl.integration_time}")
    print(f"Gain: {tsl.gain}")

def configure_sensor():
    """Configure the TSL2591 sensor."""
    if tsl:
        tsl.set_gain(GAIN_MED)  # Medium gain
        tsl.set_timing(INTEGRATIONTIME_300MS)  # 300ms integration
        print("Sensor configured with medium gain and 300ms integration time.")
    else:
        print("Sensor not available.")

def simple_read():
    """Perform a simple read from the TSL2591."""
    if tsl:
        luminosity = tsl.get_luminosity(VISIBLE)
        print(f"Luminosity: {luminosity} lux")
    else:
        print("Sensor not available.")

def check_buttons():
    """Check button states and update state."""
    global state, brightness, fade_amount

    if fluorometry_switch.value() == 1:
        time.sleep(SWITCH_DELAY)
        state = STATE_FLUOROMETRY
        print("Switch for fluorometry activated.")

    # Switch off the indicator LED
    indicator_led_fluorometry.value(0)

    if state == STATE_COLORIMETRY:
        power_led_relay.value(0)
        indicator_led_fluorometry.value(1)

    elif state == STATE_COLORIMETRY_FADE:
        # Implement fade logic
        brightness += fade_amount
        if brightness <= 0 or brightness >= 255:
            fade_amount = -fade_amount
        print(f"Brightness: {brightness}")

        power_led_relay.value(0)
        indicator_led_fluorometry.value(1)

    elif state == STATE_FLUOROMETRY:
        power_led_relay.value(1)
        indicator_led_fluorometry.value(1)

    elif state == STATE_NONE:
        power_led_relay.value(0)

    print(f"State: {state}")

def loop():
    """Main loop."""
    while True:
        simple_read()
        check_buttons()
        time.sleep(0.2)

# Program start
def main():
    print("Starting MicroPython TSL2591 Test!")
    configure_sensor()
    display_sensor_details()
    loop()

# Run the program
if __name__ == "__main__":
    main()
