
#!/usr/bin/env python

from time import sleep
import RPi.GPIO as GPIO, os, time

input_pin = 18        # pin used to read anemometer
led_pin = 25
sleep_time = 5

GPIO.setmode(GPIO.BCM)
GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  #pin that the anemometer is connected to
GPIO.setup(led_pin, GPIO.OUT)   # pin that the LED is connected to

timer = time.time()   # initialise the timer
fast_time = -1        # TODO: future use

def wind_ping(channel):
    global timer
    global fast_time
    cur_time = (time.time() - timer)  # time for half a revolution
    wind_speed = 0.667 / cur_time   # reworked from the datasheet
    if wind_speed < 200:  # add bounce detection here
        if cur_time < fast_time:
            fast_time = cur_time   
        wind_str = "%10.4f" % wind_speed    # convert the float number to a string
        wind_speed = wind_speed * 2.236936  # apply the multiplier to calculate miles per hour
        windmph_str = "%10.4f" % wind_speed
        cur_str = "%10.4f" % cur_time
        # will print the measurements to screen for each pulse detected
        print "Wind Speed: " + wind_str + " m/s, " + windmph_str + " mph, time: " + cur_str
        timer = time.time()  #reset the timer for the next revolution
        GPIO.output(led_pin, not GPIO.input(led_pin))  # alternate the LED state

GPIO.add_event_detect(input_pin,GPIO.FALLING, bouncetime=30)  #threaded event, to detect the 
  # voltage falling on anemometer (pin 18)
GPIO.add_event_callback(input_pin,wind_ping)	# tell the event to call procedure above

try:
   while True:  # loop to keep the program alive
    sleep(sleep_time)

except KeyboardInterrupt:
    GPIO.cleanup()  # reset the GPIO pins when you press ctrl+c