#!/usr/bin/python
# Show a sliding text on single 32x32 RGB led panel
# (c) 2014 Sergio Tanzilli - sergio@tanzilli.com 

import time
import sys
import os
from datetime import datetime
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import StringIO

if len(sys.argv)<2 or len(sys.argv)>5:
	print "Syntax:"
	print "  %s text r g b" % (sys.argv[0])
	quit()

font = ImageFont.truetype('Ubuntu-B.ttf', 32)

text=sys.argv[1]
r=int(sys.argv[2])
g=int(sys.argv[3])
b=int(sys.argv[4])
  
im = Image.new("RGB", (32, 32), "black")
draw = ImageDraw.Draw(im)
draw.fontmode="1" #No antialias
width, height = font.getsize(sys.argv[1])
  
x = 32

out_file = open("/sys/class/ledpanel/rgb_buffer","w")
output = StringIO.StringIO()
while True:
	x = x - 1

	if x < -(width):
		x = 32
		
	draw.rectangle((0, 0, 31, height), outline=0, fill=0)
	draw.text((x, -1), text, (r<<5,g<<5,b<<5), font=font)

	output.truncate(0)
	im.save(output, format='PPM')
	buf=output.getvalue()

	out_file.seek(0)
	out_file.write(buf[13:])

out_file.close()
