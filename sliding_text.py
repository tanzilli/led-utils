#!/usr/bin/python
# 2 digit counter example for 32x32 RGB led panel
# (c) 2014 Sergio Tanzilli - sergio@tanzilli.com 

import sys
import os
import Image, ImageDraw, ImageFont
import StringIO
import time

size = 32, 32

ttf = 'Digital Dismay.otf'
font = ImageFont.truetype(ttf, 35)

for i in range(0,100):
	im=Image.new("RGB",size,"black")

	draw = ImageDraw.Draw(im)
	#draw.line((0, 0) + im.size, fill=128, width=3)
	#draw.line((0, im.size[1], im.size[0], 0), fill=128)
	counter="%02d" % i
	draw.text((2, 0), counter, (0,0,1<<5), font=font)
	del draw

	#Save the image in .ppm format
	#im.save("output" + ".jpg")

	output = StringIO.StringIO()
	im.save(output, format='PPM')
	buf=output.getvalue()

	out_file = open("/sys/class/ledpanel/rgb_buffer","w")
	out_file.write(buf[13:])
	out_file.close()
	del im
	time.sleep(1)
