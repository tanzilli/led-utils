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
font = ImageFont.truetype("Ubuntu-B.ttf", 30)

#Count from 0 to 99
for i in range(99,-1,-1):
	
	#Create a 32x32 black image  
	im=Image.new("RGB",size,"black")

	#Create a draw object to draw primitives on the new image 
	draw = ImageDraw.Draw(im)

	#Format the counter in 2 digit
	counter="%02d" % i
	
	#Draw counter text on the panel 
	draw.text((0,0), counter, (0,0,1<<5), font=font)
	del draw

	#Generate a PPM image (a format very similar to byte array RGB we need)
	output = StringIO.StringIO()
	im.save(output, format='PPM')
	buf=output.getvalue()

	#Discard the first 13 bytes of header and save the rest (the
	#RGB array) on the ledpanel driver output buffer
	out_file = open("/sys/class/ledpanel/rgb_buffer","w")
	out_file.write(buf[13:])
	out_file.close()
	del im
	time.sleep(1)
