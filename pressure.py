import os
import glob
import sys
import re
import time
import subprocess
import MySQLdb as mdb 
import datetime

from smbus import SMBus
import time
 

databaseUsername="root" #YOUR MYSQL USERNAME, USUALLY ROOT
databasePassword="ecweather" #YOUR MYSQL PASSWORD 
databaseName="WordpressDB" #do not change unless you named the Wordpress database with some other name

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def saveToDatabase(pressure):

	con=mdb.connect("localhost", databaseUsername, databasePassword, databaseName)
        currentDate=datetime.datetime.now().date()

        now=datetime.datetime.now()
        midnight=datetime.datetime.combine(now.date(),datetime.time())
        minutes=((now-midnight).seconds)/60 #minutes after midnight, use datead$


        with con:
                cur=con.cursor()

                cur.execute("INSERT INTO pressure (pressure, humidity, dateMeasured, hourMeasured) VALUES (%s,%s,%s,%s)",(pressure,'NULL',currentDate, minutes))

		print "Saved pressure"
		return "true"



def read_pressure():
	    # Special Chars
	deg = u'\N{DEGREE SIGN}'

	# I2C Constants
	ADDR = 0x60
	CTRL_REG1 = 0x26
	PT_DATA_CFG = 0x13
	bus = SMBus(1)

	who_am_i = bus.read_byte_data(ADDR, 0x0C)
	print hex(who_am_i)
	if who_am_i != 0xc4:
	    print "Device not active."
	    exit(1)

	# Set oversample rate to 128
	setting = bus.read_byte_data(ADDR, CTRL_REG1)
	newSetting = setting | 0x38
	bus.write_byte_data(ADDR, CTRL_REG1, newSetting)

	# Enable event flags
	bus.write_byte_data(ADDR, PT_DATA_CFG, 0x07)

	# Toggel One Shot
	setting = bus.read_byte_data(ADDR, CTRL_REG1)
	if (setting & 0x02) == 0:
	    bus.write_byte_data(ADDR, CTRL_REG1, (setting | 0x02))

	# Read sensor data
	print "Waiting for data..."
	status = bus.read_byte_data(ADDR,0x00)
	# while (status & 0x08) == 0:
	#     #print bin(status)
	#     status = bus.read_byte_data(ADDR,0x00)
	#     time.sleep(0.5)

	print "Reading sensor data..."
	p_data = bus.read_i2c_block_data(ADDR,0x01,3)
	t_data = bus.read_i2c_block_data(ADDR,0x04,2)
	status = bus.read_byte_data(ADDR,0x00)
	print "status: "+bin(status)

	p_msb = p_data[0]
	p_csb = p_data[1]
	p_lsb = p_data[2]
	t_msb = t_data[0]
	t_lsb = t_data[1]

	pressure = (p_msb << 10) | (p_csb << 2) | (p_lsb >> 6)
	p_decimal = ((p_lsb & 0x30) >> 4)/4.0

	celsius = t_msb + (t_lsb >> 4)/16.0
	fahrenheit = (celsius * 9)/5 + 32

	print "Pressure and Temperature at "+time.strftime('%m/%d/%Y %H:%M:%S%z')
	print str(pressure+p_decimal)+" Pa"
	print str(celsius)+deg+"C"
	print str(fahrenheit)+deg+"F"

	return pressure+p_decimal


#check if table is created or if we need to create one
try:
	queryFile=file("createTable.sql","r")

	con=mdb.connect("localhost", databaseUsername,databasePassword,databaseName)
        currentDate=datetime.datetime.now().date()

        with con:
		line=queryFile.readline()
		query=""
		while(line!=""):
			query+=line
			line=queryFile.readline()

		cur=con.cursor()
		cur.execute(query)	

        	#now rename the file, because we do not need to recreate the table everytime this script is run
		queryFile.close()
        	os.rename("createTable.sql","createTable.sql.bkp")


except IOError:
	pass #table has already been created



saveToDatabase(read_pressure())
