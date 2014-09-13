#!/usr/bin/python
# Sliding digital clock on single 32x32 RGB led panel - Demo version
# (c) 2014 Sergio Tanzilli - sergio@tanzilli.com 

import time
import sys
import os
from datetime import datetime
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import StringIO
import select

print "clock_demo.py"
print "  press ENTER to exit"

#Use a TTF font
font = ImageFont.truetype('Ubuntu-B.ttf', 30)

#Initial color
r=1
g=1
b=1

#Create a 32x32 black image  
im = Image.new("RGB", (32, 32), "black")
draw = ImageDraw.Draw(im)

#Get the dimension of the finale clock image
width, height = font.getsize("88:88:88")
 
#Read the system date 
def format_time():
    d = datetime.now()
    return "{:%H:%M:%S}".format(d)
 
message = format_time()

#Set the start point of scrolling text
x = 32
y= -3

colore=0

#Open the driver image buffer
#ledpanel linux driver need to be executed
#https://github.com/tanzilli/ledpanel 
out_file = open("/sys/class/ledpanel/rgb_buffer","w")

#Create an image buffer in ram
output = StringIO.StringIO()
while True:
	x = x - 1

	if x < -(width):
		x = 32
		message = format_time()
		if (colore==0):
			r=1
			g=0
			b=0
		if (colore==1):
			r=0
			g=1
			b=0
		if (colore==2):
			r=1
			g=1
			b=0
		if (colore==3):
			r=0
			g=0
			b=1
		if (colore==4):
			r=1
			g=0
			b=1
		if (colore==5):
			r=0
			g=1
			b=1
		if (colore==6):
			r=1
			g=1
			b=1
			font=font_1			
		if (colore==7):
			colore=0
			
	
	#Delete the previous written	
	draw.rectangle((0, 0, 31, height), outline=0, fill=0)
	
	#Write inside the image the current time in bitmap
	draw.text((x,y), message, (r<<5,g<<5,b<<5), font=font)

	#Save the bitmao on a dummy buffer in PPM
	#format (I used this because is very similar to
	#a RGB byte array
	output.truncate(0)
	im.save(output, format='PPM')
	buf=output.getvalue()

	out_file.seek(0)
	#Discard the first 13 header byte and use just the RGB
	#byte array
	out_file.write(buf[13:])
	
	time.sleep(0.01)
	
	# If there's input ready, do something, else do something
	# else. Note timeout is zero so select won't block at all.
	while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
		#out_file.write(buf[13:])
		out_file.close()
		exit(0)
	else:
	  pass
	
