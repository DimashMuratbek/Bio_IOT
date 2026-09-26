from machine import Pin, Timer
import time

# Define global variables
flow_frequency = 0  # Measures flow meter pulses
l_hour = 0          # Calculated liters/hour
flowmeter_pin = 39  # Flow Meter Pin number
cloopTime = 0   # Loop time for calculating flow

# Interrupt handler function
def flow(pin):
    global flow_frequency
    flow_frequency += 1

# Setup function equivalent
def setup():
    global cloopTime
    # Configure the flowmeter pin as input with a pull-down resistor
    flowmeter = Pin(flowmeter_pin, Pin.IN, Pin.PULL_DOWN)
    flowmeter.irq(trigger=Pin.IRQ_RISING, handler=flow)  # Attach interrupt

    cloopTime = time.ticks_ms()  # Initialize cloopTime

# Loop function equivalent
def loop():
    global cloopTime, flow_frequency, l_hour

    currentTime = time.ticks_ms()
    # Every second, calculate and print liters/hour
    if time.ticks_diff(currentTime, cloopTime) >= 1000:
        cloopTime = currentTime  # Update cloopTime
        # Pulse frequency (Hz) = 7.5Q, Q is flow rate in L/min. (Results in +/- 3% range)
        l_hour = int((flow_frequency * 60) / 7.5)  # Calculate liters/hour
        flow_frequency = 0  # Reset counter

        # Print liters/hour to the console
        print(f"{l_hour} L/hour")

# Main program
if __name__ == "__main__":
    setup()
    while True:
        loop()  