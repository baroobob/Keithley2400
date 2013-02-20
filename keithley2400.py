# Copyright 2010 Jim Bridgewater

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# 12/27/10 Jim Bridgewater
# Added figure parameter to read function so update_graph function can
# use it.

# 05/31/10 Jim Bridgewater
# Added auto detection of the serial port

# 08/04/08 Jim Bridgewater
# Adapted this code originally written for the Keithley 617 so that it
# provides a similar interface for the Keithley 2400. 

#################################################################
# The user functions defined in this module are:
#################################################################
# close_connection():
# current_mode():
# enable_live_readings():
# enable_voltage_source():
# disable_voltage_source():
# open_connection():
# read(interval = 0, samples = 1):
# resistance_mode():
# set_voltage_source(voltage):
# voltage_mode():

#################################################################
# Import libraries
#################################################################
import time
import prologixGPIBUSB as gpib
from errors import Error

#################################################################
# Global Declarations
#################################################################
Debug = 0  # set to 1 to enable printing of error codes
READING_AVAILABLE = 1 << 6

#################################################################
# Function definitions
#################################################################

# Close the connection to the keithley.
def close_connection():
  gpib.close_connection()


# Set the Keithley to measure current.
def current_mode():
  gpib.write("SOUR:FUNC VOLT")
  gpib.write("SOUR:VOLT 0")
  gpib.write("CONF:CURR")
  gpib.write("FORM:ELEM CURR")
  time.sleep(1)


# Open the connection to the Prologix USB/GPIB interface and configure
# it to communicate with the Keithley 2400.
def open_connection():
  gpib.open_connection()
  gpib.set_address(24)
  gpib.clear_selected_device()  # clear keithley
  gpib.write("*IDN?")           # ask instrument to identify itself
  reading = gpib.readline()
  if "KEITHLEY INSTRUMENTS INC.,MODEL 2400" in reading:    
    gpib.write("OUTP ON")       # Enable the Keithley's output
  else:
    raise Error("ERROR: The Keithley 2400 is not responding.")    
    

# Set up the Keithley 2400 to provide live readings.
def enable_live_readings():
  gpib.write("ARM:COUN INF")  # infinite arm count
  gpib.write("TRIG:DEL 0")    # zero trigger delay
  gpib.write("INIT")          # start measurements


# This function is a placeholder to maintain compatibility with the 
# keithley617 module.
def enable_voltage_source():
  pass


# This function is primarily a placeholder to maintain compatibility 
# with the keithley617 module, it sets the output of the Keithley's 
# internal voltage source to zero Volts.
def disable_voltage_source():
  gpib.write("SOUR:VOLT 0")


# This function is the default value of the function parameter for the
# read function below.
def do_nothing(*dummy):
  pass


# Read a specified number of measurement samples from the keithley at a
# specified sample period.
def read(interval = 0, samples = 1, update_graph = do_nothing, *args):
  gpib.write("ARM:COUN 1")              # arm instrument
  gpib.write("TRIG:COUN %d" % samples)  # setup trigger count
  gpib.write("TRIG:DEL %f" % interval)  # setup trigger delay
  Time = []
  Data = []
  CurrentSample = 0
  gpib.write("READ?")          # start measurement
  while len(Data) < samples:
    while CurrentSample < len(Data):
      update_graph(Time[CurrentSample], Data[CurrentSample], figure)
      CurrentSample = CurrentSample + 1
    time.sleep(interval)
    DataString = gpib.readline()
    DataString = DataString.split(',')
    for i in range(len(DataString)):
      if len(DataString[i]) > 0:
        #print DataString[i]
        if DataString[i] != '\x00\x00\x00':  # some 2400s return this if no data
          Time.append(float(len(Data) * interval))
          Data.append(float(DataString[i]))
  while CurrentSample < len(Data):
    update_graph(Time[CurrentSample], Data[CurrentSample], *args)
    CurrentSample = CurrentSample + 1

  if samples > 1:
    return Time, Data
  else:
    return Data[0]

  
# Set the Keithley to measure resistance.
def resistance_mode():
  gpib.write("CONF:RES")
  gpib.write("FORM:ELEM RES")


# Set the value of the Keithley's internal voltage source.
def set_voltage_source(voltage):
  if abs((voltage / 5e-6) - round(voltage / 5e-6)) > 1e-10:
    print 'Warning: The voltage source in the Keithley 2400 has a ' \
    'maximum resolution of 5 uV.'
  gpib.write("SOUR:VOLT " + str(voltage))


# This function sets the Keithley to measure voltage.
def voltage_mode():
  gpib.write("SOUR:FUNC CURR")
  gpib.write("SOUR:CURR 0")
  gpib.write("CONF:VOLT")
  gpib.write("FORM:ELEM VOLT")
  time.sleep(1)


################# OLD STUFF BELOW ######################

# This function is called by the read function in the event that 
# samples > 1.
def read_old(interval = 0, samples = 1, update_graph = do_nothing):
  RAV = 1 << 6
  gpib.write("TRIG:COUN 1")      # setup trigger count
  gpib.write("TRIG:DEL %f" % interval)  # setup trigger delay
  Time = []
  Data = []
  CurrentSample = 1
  Datum = gpib.readline()
  gpib.write("INIT")          # start measurement
  while CurrentSample <= samples:
    reading_available = 0
    while not reading_available:
      #print str(measurement_event) + ", " + str(reading_available)
      time.sleep(interval)
      gpib.write("STAT:MEAS?")    # read measurement event register
      gpib.write("++read 10")
      measurement_event = int(gpib.readline())
      reading_available = measurement_event & RAV
    gpib.write("FETC?")
    gpib.write("++read 10")
    gpib.write("INIT")          # start measurement
    Datum = gpib.readline()
    #print Datum
    #Data = Data + [float(Datum[4:Datum.find(',')])]
    Data = Data + [float(Datum)]
    Time = Time + [(CurrentSample - 1) * interval]
    CurrentSample = CurrentSample + 1
    update_graph(Time[-1], Data[-1])     # call graph update function 
  gpib.write("ARM:COUN INF")      # return instrument to live mode
  gpib.write("TRIG:DEL 0")
  gpib.write("INIT")          # start measurements
  if samples > 1:
    return Time, Data
  else:
    return float(Datum)


# This function is called by the read function in the event that 
# samples = 1.
def read_one(interval = 0):
  #gpib.write("ARM:COUN 1")
  #gpib.write("ARM:SOUR BUS")
  gpib.write("TRIG:COUN 1")      # setup trigger count
  gpib.write("TRIG:DEL %f" % interval)  # setup trigger delay
  gpib.write("INIT")          # start measurement
  #gpib.write("*TRG")

  gpib.write("STAT:MEAS?")        # read measurement event register
  gpib.write("++read 10")
  measurement_event = int(gpib.readline())
  RAV = 1 << 6
  reading_available = measurement_event & RAV
  while not reading_available:
    #print str(measurement_event) + ", " + str(reading_available)
    time.sleep(interval)
    gpib.write("STAT:MEAS?")      # read measurement event register
    gpib.write("++read 10")
    measurement_event = int(gpib.readline())
    reading_available = measurement_event & RAV
  #gpib.write("*CLS")          # clear event registers
  #time.sleep(interval)
  gpib.write("FETC?")
  gpib.write("++read 10")
  Datum = gpib.readline()
  print "reading: " + Datum
  return Datum


# This function reads values from the Keithley at a specified sample interval
# (in seconds). All timing is controlled by the Keithley. If only one sample is 
# requested the function returns the second sample taken by the Keithley, 
# otherwise it returns the first n samples.
# For example, Read(10) returns one sample that is taken 10 seconds after the
# function is called while Read(10, 2) returns two samples, the first one is 
# taken immediately when the function is called and the second sample is taken
# 10 seconds later.
# If more than one sample is requested, the allowed values of the interval 
# parameter are 0, 1, 10, 60, 600, and 3600. If only one sample is requested,
# the allowed values of interval are 0 through 99.
# The allowed values of the samples parameter are 1 to 100.
def read_old(interval = 0, samples = 1, update_graph = do_nothing):
  if samples > 1:
    return read_multiple(interval, samples, update_graph)
  else:
    return read_one(interval)


