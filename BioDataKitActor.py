#!/usr/bin/env python3

import time
import math
import colorsys
import sys
import ST7735
try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
#from pms5003 import PMS5003, ReadTimeoutError as pmsReadTimeoutError, SerialTimeoutError
from enviroplus import gas
from subprocess import PIPE, Popen
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from fonts.ttf import RobotoMedium as UserFont
import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class BioDataKitActor(object):
    def __init__(self, *args, **kwargs):
        self.timeout = 1000 * 60 * 10 # run every 10 min
        # BME280 temperature/pressure/humidity sensor
        self.bme280 = BME280()

        self.proximity = ltr559.get_proximity()

        # PMS5003 particulate sensor
        #self.pms5003 = PMS5003()
        #time.sleep(1.0)

        # Create ST7735 LCD display class
        self.st7735 = ST7735.ST7735(
            port=0,
            cs=1,
            dc=9,
            backlight=12,
            rotation=270,
            spi_speed_hz=10000000
        )
        # Initialize display
        self.st7735.begin()

        self.WIDTH = self.st7735.width
        self.HEIGHT = self.st7735.height

        # Set up canvas and font
        self.img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)
        self.font_size_small = 10
        self.font_size_large = 20
        self.font = ImageFont.truetype(UserFont, self.font_size_large)
        self.smallfont = ImageFont.truetype(UserFont, self.font_size_small)
        self.x_offset = 2
        self.y_offset = 2

        message = ""

        # The position of the top bar
        self.top_pos = 25
        
        # compensate vars (from enviromonitor)
        self.temp_offset = 2.3
        self.comp_temp_cub_a = -0.0001
        self.comp_temp_cub_b = 0.0037
        self.comp_temp_cub_c = 1.00568
        self.comp_temp_cub_d = -6.78291
        self.comp_temp_cub_d = self.comp_temp_cub_d + self.temp_offset
        # Quadratic polynomial hum comp coefficients
        self.comp_hum_quad_a = -0.0032
        self.comp_hum_quad_b = 1.6931
        self.comp_hum_quad_c = 0.9391

        # Create a values dict to store the data
        self.variables = ["temperature",
                     "pressure",
                     "humidity",
                     "light",
                     "oxidised",
                     "reduced",
                     "nh3"]

        self.units = ["C",
                 "hPa",
                 "%",
                 "Lux",
                 "kO",
                 "kO",
                 "kO",
                 "ug/m3",
                 "ug/m3",
                 "ug/m3"]

        # Define your own warning limits
        # The limits definition follows the order of the variables array
        # Example limits explanation for temperature:
        # [4,18,28,35] means
        # [-273.15 .. 4] -> Dangerously Low
        # (4 .. 18]      -> Low
        # (18 .. 28]     -> Normal
        # (28 .. 35]     -> High
        # (35 .. MAX]    -> Dangerously High
        # DISCLAIMER: The limits provided here are just examples and come
        # with NO WARRANTY. The authors of this example code claim
        # NO RESPONSIBILITY if reliance on the following values or this
        # code in general leads to ANY DAMAGES or DEATH.
        self.limits = [[4, 18, 28, 35],
                  [250, 650, 1013.25, 1015],
                  [20, 30, 60, 70],
                  [-1, -1, 30000, 100000],
                  [-1, -1, 40, 50],
                  [-1, -1, 450, 550],
                  [-1, -1, 200, 300],
                  [-1, -1, 50, 100],
                  [-1, -1, 50, 100],
                  [-1, -1, 50, 100]]

        # RGB palette for values on the combined screen
        self.palette = [(0, 0, 255),           # Dangerously Low
                   (0, 255, 255),         # Low
                   (0, 255, 0),           # Normal
                   (255, 255, 0),         # High
                   (255, 0, 0)]           # Dangerously High

        self.values = {}
        for v in self.variables:
            self.values[v] = [1] * self.WIDTH
        self.cpu_temps = [self.get_cpu_temperature()] * 5
        # Tuning factor for compensation. Decrease this number to adjust the
        # temperature down, and increase to adjust up
        self.factor = 2.25
    
        self.mode = 0


    def send_osc(idx):
        variable = variables[idx]
        value = values[variable][-1]
        unit = units[idx]
        print(variable, value, unit)
        msg = oscbuildparse.OSCMessage("/{}".format(variable), None, (value, unit) )
        for c in osc_clients:
            osc_send(msg, c)

    # Displays data and text on the 0.96" LCD
    def display_text(self, variable, data, unit):
        # Maintain length of list
        values[variable] = values[variable][1:] + [data]
        # Scale the values for the variable between 0 and 1
        vmin = min(values[variable])
        vmax = max(values[variable])
        colours = [(v - vmin + 1) / (vmax - vmin + 1) for v in values[variable]]
        # Format the variable name and value
        message = "{}: {:.1f} {}".format(variable[:4], data, unit)
        logging.info(message)
        self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), (255, 255, 255))
        for i in range(len(colours)):
            # Convert the values to colours from red to blue
            colour = (1.0 - colours[i]) * 0.6
            r, g, b = [int(x * 255.0) for x in colorsys.hsv_to_rgb(colour, 1.0, 1.0)]
            # Draw a 1-pixel wide rectangle of colour
            self.draw.rectangle((i, self.top_pos, i + 1, self.HEIGHT), (r, g, b))
            # Draw a line graph in black
            line_y = self.HEIGHT - (self.top_pos + (colours[i] * (self.HEIGHT - self.top_pos))) + self.top_pos
            self.draw.rectangle((i, line_y, i + 1, line_y + 1), (0, 0, 0))
        # Write the text at the top in black
        self.draw.text((0, 0), message, font=self.font, fill=(0, 0, 0))
        st7735.display(self.img)


    # Saves the data to be used in the graphs later and prints to the log
    def save_data(self, idx, data):
        variable = self.variables[idx]
        # Maintain length of list
        self.values[variable] = self.values[variable][1:] + [data]
        unit = self.units[idx]
        message = "{}: {:.1f} {}".format(variable[:4], data, unit)
        #logging.info(message)


    # Displays all the text on the 0.96" LCD
    def display_everything(self):
        self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), (0, 0, 0))
        column_count = 2
        row_count = (len(self.variables) / column_count)
        for i in range(len(self.variables)):
            variable = self.variables[i]
            data_value = self.values[variable][-1]
            unit = self.units[i]
            x = self.x_offset + ((self.WIDTH // column_count) * (i // row_count))
            y = self.y_offset + ((self.HEIGHT / row_count) * (i % row_count))
            message = "{}: {:.1f} {}".format(variable[:4], data_value, unit)
            lim = self.limits[i]
            rgb = self.palette[0]
            for j in range(len(lim)):
                if data_value > lim[j]:
                    rgb = self.palette[j + 1]
            self.draw.text((x, y), message, font=self.smallfont, fill=rgb)
        self.st7735.display(self.img)


    # Get the temperature of the CPU for compensation
    def get_cpu_temperature(self):
        process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
        output, _error = process.communicate()
        return float(output[output.index('=') + 1:output.rindex("'")])

    def adjusted_temperature(self):
        raw_temp = self.bme280.get_temperature()
        #comp_temp = comp_temp_slope * raw_temp + comp_temp_intercept
        comp_temp = (self.comp_temp_cub_a * math.pow(raw_temp, 3) + self.comp_temp_cub_b * math.pow(raw_temp, 2) +
                     self.comp_temp_cub_c * raw_temp + self.comp_temp_cub_d)
        return comp_temp
        
    def adjusted_humidity(self):
        raw_hum = self.bme280.get_humidity()
        #comp_hum = comp_hum_slope * raw_hum + comp_hum_intercept
        comp_hum = self.comp_hum_quad_a * math.pow(raw_hum, 2) + self.comp_hum_quad_b * raw_hum + self.comp_hum_quad_c
        return min(100, comp_hum)
    
    def process_sensor(self):
        # One mode for each variable
        mode = 0
        oscdata = []
        # variable = "temperature"
        unit = "C"
        #data = self.bme280.get_temperature()
        data = self.adjusted_temperature()
        self.save_data(mode, data)
        #self.display_everything()
        #return("/{}".format(self.variables[mode]), [data, unit])
        oscdata.extend([data, unit])

        mode = 1
        #if mode == 1:
        # variable = "pressure"
        unit = "hPa"
        data = self.bme280.get_pressure()
        self.save_data(mode, data)
        #self.display_everything()
        #return("/{}".format(self.variables[mode]), [data, unit])
        oscdata.extend([data, unit])

        mode = 2
        # variable = "humidity"
        unit = "%"
        #data = self.bme280.get_humidity()
        data = self.adjusted_humidity()
        self.save_data(mode, data)
        #self.display_everything()
        #return("/{}".format(self.variables[mode]), [data, unit])
        oscdata.extend([data, unit])

        mode = 3
        # variable = "light"
        unit = "Lux"
        if self.proximity < 10:
            data = ltr559.get_lux()
        else:
            data = 1
        self.save_data(mode, data)
        #self.display_everything()
        #return("/{}".format(self.variables[mode]), [data, unit])
        oscdata.extend([data, unit])

        mode = 4
        # variable = "oxidised"
        unit = "kO"
        data = gas.read_all()
        data = data.oxidising / 1000
        self.save_data(mode, data)
        #self.display_everything()
        #return("/{}".format(self.variables[mode]), [data, unit])
        oscdata.extend([data, unit])

        mode = 5
        # variable = "reduced"
        unit = "kO"
        data = gas.read_all()
        data = data.reducing / 1000
        self.save_data(mode, data)
        #self.display_everything()
        #return("/{}".format(self.variables[mode]), [data, unit])
        oscdata.extend([data, unit])

        mode = 6
        variable = "nh3"
        unit = "kO"
        data = gas.read_all()
        data = data.nh3 / 1000
        self.save_data(mode, data)
        self.display_everything()
        #return("/{}".format(self.variables[mode]), [data, unit])
        oscdata.extend([data, unit])

        return ("/enviro", oscdata)

    def handleTimer(self, *args, **kwargs):
        #self.mode +=1
        #self.mode %= len(self.variables)
        return self.process_sensor()

    def handleStop(self, *args, **kwargs):
        pass

