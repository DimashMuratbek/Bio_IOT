# Program to read the algae concentration inline.
# Version: v1 
# Written by: J. Hekman

#what is missing BME280 should be integrated.

from machine import Pin, ADC, RTC
from time import sleep, ticks_ms, ticks_diff
import random
import math
from tsl2591 import Tsl2591

rtc = RTC()
rtc.init((2024, 09, 23, 12, 51, 0, 0, 0))  # Set RTC time directly
start_time_ms = ticks_ms()  # Track elapsed time in milliseconds

led = Pin(5, Pin.OUT)
relayPump = Pin(2, Pin.OUT)
POMP_TIME_FOR_HOMOGENEUS_SOLUTION = 15
MEASURING_FREQUENCY_SEC = 900
ON = 1
OFF = 0

# settings for flashing
DEBUG = False  # print information to the serial port
STORE_VALUES = True  # store values on ESP32
SIMULATIONS = False
PRINT_ALL_DATA_VARIABLES = True

# Light sensor settings
FULL_SPECTRUM_BLANK = 23259 # 3d printed cuvet 6335.80 # real cuvet with in and output 18600
IR_SPECTRUM_BLANK = 527 # 3d printed cuvet 144.2     # real cuvet with in and output  403

if not SIMULATIONS:
    tsl = Tsl2591('lux-1')  # Initialize the sensor

# pH and Conductivity sensor configuration
pH_pin = 36
cond_pin = 39
adcPH = ADC(Pin(pH_pin))
adcCond = ADC(Pin(cond_pin))

for adc in [adcPH, adcCond]:
    adc.atten(ADC.ATTN_11DB)  # Set ADC to 3.3V range

pH_SLOPE = -0.0051  # Adjust based on calibration
pH_INTERCEPT = 15.449
COND_SLOPE = 0.1
COND_INTERCEPT = 100


# Combined function for sensor reading (DRY principle)
def read_sensor(adc, slope, intercept, sensor_name):
    adc_value = adc.read()
    result = adc_value * slope + intercept
    if DEBUG:
        print(f"{sensor_name}_ADC: {adc_value}, {sensor_name}: {result}")
    return result

# Function to handle light sensor readings
def read_optical_density(samples):
    led.value(ON)
    sleep(1)
    average_ir, average_full = 0, 0
    for _ in range(samples):
        tempFull, tempIR = tsl.get_full_luminosity() if not SIMULATIONS else (random.random(), random.random())
        average_ir += tempIR
        average_full += tempFull
    
    average_ir /= samples
    average_full /= samples
    
    if DEBUG:
        print(f"average_ir: {average_ir}, average_full: {average_full}")
    led.value(OFF)
    return average_full, average_ir

# Combine the extinction calculation into a single function
def convert_to_extinction(spectrum, blank):
    transmission = spectrum / blank
    # convert to extinction and return extinction instead of transmission
    return transmission

# Density measurement using the pump
def measure_density():
    relayPump.value(ON)
    sleep(POMP_TIME_FOR_HOMOGENEUS_SOLUTION)
    
    full_spectr, ir_spectr = read_optical_density(5)
    E_full = convert_to_extinction(full_spectr, FULL_SPECTRUM_BLANK)
    E_ir = convert_to_extinction(ir_spectr, IR_SPECTRUM_BLANK)
    
    relayPump.value(OFF)
    return full_spectr, E_full, ir_spectr, E_ir

# Tracking elapsed time in seconds
def get_elapsed_time():
    return ticks_diff(ticks_ms(), start_time_ms) // 1000  # Convert to seconds

# Open the file once, append throughout the loop

while True:
    elapsed_time = get_elapsed_time()  # Track the time in seconds
      # Read pH, Conductivity, and optical density
    pH = read_sensor(adcPH, pH_SLOPE, pH_INTERCEPT, "pH")
    cond = read_sensor(adcCond, COND_SLOPE, COND_INTERCEPT, "Conductivity") # not present but example of additional ADC sensor
    raw_full, extinction_full, raw_ir, extinction_ir = measure_density()
            
    if STORE_VALUES == True:	
        f = open('datafile.csv', 'a')
        
        if (elapsed_time < 20):
            store_headers = f"elapsed_time, pH, cond, raw_full, extinction_full, raw_ir, extinction_ir, \n"
            f.write(store_headers)
        # Format and store values in CSV
        data_string = f"{elapsed_time}, {pH}, {cond}, {raw_full}, {extinction_full}, {raw_ir}, {extinction_ir}\n"
        f.write(data_string)
                
        f.close()
            
    # Print variables with headers aligned
    if PRINT_ALL_DATA_VARIABLES:
        headers = (
                "Time (s)\tpH\t\tConductivity\tRaw Full Spectr\tExtinction Full\tRaw IR Spectr\tExtinction IR"
        )
        values = (
                f"{elapsed_time}\t\t{pH:.2f}\t\t{cond:.2f}\t\t{raw_full:.2f}\t\t{extinction_full:.2f}\t\t{raw_ir:.2f}\t\t{extinction_ir:.2f}"
        )
        print(headers)
        print(values)
            
    sleep(MEASURING_FREQUENCY_SEC)        

