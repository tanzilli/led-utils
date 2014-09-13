#!/usr/bin/python
# Image converter for single 32x32 RGB led panel
# (c) 2014 Sergio Tanzilli - sergio@tanzilli.com 

import sys
import tty
import termios
import os
import StringIO
from PIL import Image
from PIL import ImageEnhance
import PIL.ImageOps    

size = 32, 32

def get1char():
	fd = sys.stdin.fileno()
	old_settings = termios.tcgetattr(fd)

	try:
		tty.setraw(sys.stdin.fileno())
		ch = sys.stdin.read(1)
	finally:
		termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
	return ch


if len(sys.argv)<2 or len(sys.argv)>2:
	print "Syntax:"
	print "  %s imagefile" % (sys.argv[0])
	quit()
		
filename=os.path.splitext(os.path.basename(sys.argv[1]))[0]

im=Image.open(sys.argv[1]).convert('RGB')
#im.thumbnail(size,Image.ANTIALIAS)
im.thumbnail(size)

brightness=1.0
contrast=1.0
color=1.0
sharpness=1.0
angle=0
invert=0
out_counter=0;

im_final=im

while True:
	print ""
	print "------------------------"
	print "[1] <- Brightness -> [2]"
	print "[3] <-  Contrast  -> [4]"
	print "[5] <-   Color    -> [6]"
	print "[7] <- Sharpness  -> [8]"
	print "[q] <-   Rotate   -> [w]"
	print "[i] Invert color        "
	print "[r] Reset               "
	print "[s] Save                "
	print "------------------------"
	print ""
	
	#Generate a PPM image (a format very similar to byte array RGB we need)
	output = StringIO.StringIO()
	im_final.save(output, format='PPM')
	buf=output.getvalue()

	#Discard the first 13 bytes of header and save the rest (the
	#RGB array) on the ledpanel driver output buffer
	out_file = open("/sys/class/ledpanel/rgb_buffer","w")
	out_file.write(buf[13:])
	out_file.close()

	print "Select (space exit): ",
	input_char=get1char()

	if (input_char=="1"):
		if (brightness>0.0):
			brightness=brightness-0.1

	if (input_char=="2"):
		if (brightness<1.0):
			brightness=brightness+0.1
	
	if (input_char=="3"):
		if (contrast>0.0):
			contrast=contrast-0.1

	if (input_char=="4"):
		if (contrast<1.0):
			contrast=contrast+0.1

	if (input_char=="5"):
		if (color>0.0):
			color=color-0.1

	if (input_char=="6"):
		if (color<1.0):
			color=color+0.1

	if (input_char=="7"):
		if (sharpness>0.0):
			sharpness=sharpness-0.1

	if (input_char=="8"):
		if (sharpness<1.0):
			sharpness=sharpness+0.1

	if (input_char=="q"):
		if (angle<180):
			angle=angle+5

	if (input_char=="w"):
		if (angle>-180):
			angle=angle-5

	if (input_char=="s"):
		out_filename="panel_%04d.rgb" % out_counter
		out_counter=out_counter+1;
		
		output = StringIO.StringIO()
		im_final.save(output, format='PPM')
		buf=output.getvalue()

		out_file = open(out_filename,"w")
		out_file.write(buf[13:])
		out_file.close()

		print "Saved on %s" % out_filename

	if (input_char=="r"):
		if (angle>-180):
			brightness=1.0
			contrast=1.0
			color=1.0
			sharpness=1.0
			angle=0
			invert=0

	if (input_char=="i"):
		if (invert==1):
			invert=0;
		else:		
			invert=1;

	print angle

	im_final=ImageEnhance.Brightness(im).enhance(brightness)
	im_final=ImageEnhance.Brightness(im_final).enhance(contrast)
	im_final=ImageEnhance.Color(im_final).enhance(color)
	im_final=ImageEnhance.Sharpness(im_final).enhance(sharpness)

	if (invert==1):
		im_final = PIL.ImageOps.invert(im_final)

	im_final=im_final.rotate(angle)

	if (input_char=="Q" or input_char==" "):
		exit() 



