#!/usr/bin/python

import time
from datetime import datetime
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import StringIO
import sys

if len(sys.argv)<2 or len(sys.argv)>2:
	print "Syntax:"
	print "  %s text" % (sys.argv[0])
	quit()

font = ImageFont.truetype('Ubuntu-B.ttf', 32)
  
im = Image.new("RGB", (32, 32), "black")
draw = ImageDraw.Draw(im)

message=sys.argv[1]
width, ignore = font.getsize(message)

x = 32
while True:
	x = x - 2
	if x < -(width):
		x = 32
		
	draw.rectangle((0, 0, 31, 31), outline=0, fill=0)
	draw.text((x, -4), message, (2<<5,1,0), font=font)

	output = StringIO.StringIO()
	im.save(output, format='PPM')
	buf=output.getvalue()

	out_file = open("/sys/class/ledpanel/rgb_buffer","w")
	out_file.write(buf[13:])
	out_file.close()

	time.sleep(0.001)
