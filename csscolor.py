#!/usr/bin/python
# Fill with a CSS color

import sys

if len(sys.argv)<2 or len(sys.argv)>2:
	print "Syntax:"
	print "  %s \"csscolor\"" % (sys.argv[0])
	print
	print "Example:"
	print "  %s \"#FF00000\"" % (sys.argv[0])
	quit()

#Transform a 8 bit/color CSS value 
#in 3 binary value (4 bit/color)

color=sys.argv[1]
R=int("0x%s" % (color[1:3]),16)>>4
G=int("0x%s" % (color[3:5]),16)>>4
B=int("0x%s" % (color[5:7]),16)>>4

#print "%02X %02X %02X" % (R,G,B)

#Turn on all the led with the same color
buf = bytearray()
for i in range(1024):
	buf.append(R)
	buf.append(G)
	buf.append(B)

out_file = open("/sys/class/ledpanel/rgb_buffer","w")
out_file.write(buf)
out_file.close()
