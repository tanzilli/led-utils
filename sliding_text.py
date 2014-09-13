#!/usr/bin/python
# 2 digit counter example for 32x32 RGB led panel
# (c) 2014 Sergio Tanzilli - sergio@tanzilli.com 

import sys
import os
import Image, ImageDraw, ImageFont
import StringIO
import time

#Panel size
size = 32, 32

#Load a TTF font
font = ImageFont.truetype("Ubuntu-B.ttf", 34)

#Send x times the same message
for i in range(0,100):
	
	#Create a 32x32 black image  
	im=Image.new("RGB",size,"black")

	#Create a draw object to draw primitives on the new image 
	draw = ImageDraw.Draw(im)
	counter="%02d" % i
	
	#Draw the full message text on the image 
	draw.text((2, 0), counter, (0,0,1<<5), font=font)
	del draw

	output = StringIO.StringIO()
	im.save(output, format='PPM')
	buf=output.getvalue()

	out_file = open("/sys/class/ledpanel/rgb_buffer","w")
	out_file.write(buf[13:])
	out_file.close()
	del im
	time.sleep(1)
