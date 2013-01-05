# weather_stick: code that drives a 'weather stick' which consists
# of addressable RGB LEDs (from the Adafruit LED belt kit) to 
# display the weather scraped from the BBC.
#
# Copyright (c) 2013 John Graham-Cumming

from bs4 import BeautifulSoup
import urllib2
import sys

sys.path.append("./quick2wire")
from quick2wire.spi import *

# This is the location code in the BBC weather URL for the location to
# be displayed.

location_code = '2643743';
weather_base = 'http://www.bbc.co.uk/weather/%s'

soup = BeautifulSoup(urllib2.urlopen(weather_base % location_code))

# Finds the table that contains the hours and returns the list of the
# available hours. The table looks something like:
#
# <tr class="time">
#   <th class="row-title">Time</th>
# <th class="value hours-1"><span class="hour">18</span>
# <span class="mins">00</span>
def find_hours(s):
    return [x.string for x in s.find("tr", class_="time").find_all("span", class_="hour")]

# Finds the table that contains the weather conditions and extracts a
# textual description of the weather condition from the image tag
# title. It looks something like:
#
# <tr class="weather-type">
#   <th class="row-title">Weather Conditions</th>
# <td class="hours-1"><span class="content" style="bottom:-4.5px">
#   <img src="http://static.bbci.co.uk/weather/0.5.176/images/icons/individual_32_icons/en_on_light_bg/0.png" alt="Clear Sky" title="Clear Sky">
#   </span></td>
def find_conditions(s):
    return [ x['title'] for x in s.find("tr", class_="weather-type").find_all("img")]

hours = find_hours(soup)
conditions = find_conditions(soup)

# Report a fatal error and exit
def fatal(s):
    sys.exit(s)

if len(hours) != len(conditions):
    fatal('Hours and conditions do not match')
    
# Translate BBC weather conditions into a small number of simpler
# conditions that can be displayed as colors.
def simplify(c):
    return {
        'Clear Sky':         'sunny',
        'Sunny':             'sunny',
        'Sunny Intervals':   'sunny',

        'Partly Cloudy':     'cloud',
        'White Cloud':       'cloud',
        'Grey Cloud':        'cloud',
        'Mist':              'cloud',
        'Fog':               'cloud',

        'Thundery Shower':   'light rain',
        'Drizzle':           'light rain',
        'Light Rain':        'light rain',
        'Light Rain Shower': 'light rain',

        'Heavy Rain':        'heavy rain',
        'Heavy Rain Shower': 'heavy rain',

        'Sleet':             'snow',
        'Light Snow':        'snow',
        'Light Snow Shower': 'snow',
        }.get(c, 'unknown')

weather = {}
for h, c in zip(hours, conditions):
    weather[h] = simplify(c)

show = ['08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']

# Pixel color on the wire is Green Red Blue with 8 bits per pixel
# and green the top 8 bits of a 24 bit number. 
def grb(r, g, b):
    return [g, r, b]

# Translate the output of simplify into a color value to be 
# used on the LED strip
def to_color(s):
    return {
        'sunny':      grb(255, 255, 0),   # Yellow
        'cloud':      grb(220, 220, 22),  # Greyish
        'light rain': grb(0, 255, 255),   # Cyan
        'heavy rain': grb(0, 0, 255),     # Dark blue
        'snow':       grb(255, 255, 255), # White
        'unknown':    grb(255, 0, 0)      # Red
        }[s]

colors = []

for h in show:
    if h in weather:
        colors.extend(to_color(weather[h]))
    else:
        colors.extend(grb(0, 0, 0))

print colors

strip = SPIDevice(0, 0)
strip.speed_hz = 2000000
strip.close_mode = SPI_MODE_0
strip.transaction(writing_bytes(colors))
strip.close()

