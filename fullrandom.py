import time
import random

while True:
	R=random.randint(0,7)
	G=random.randint(0,7)
	B=random.randint(0,7)
	print ("RGB = [%d %d %d]") % (R,G,B)
	
	R=R<<5
	G=G<<5
	B=B<<5
	
	i=0
	buf=bytearray(32*32*3)

	for row in range (0,32):
		for col in range (0,32):
				buf[i+0]=R
				buf[i+1]=G
				buf[i+2]=B
				i=i+3

	out_file = open("/sys/class/ledpanel/rgb_buffer","w")
	out_file.write(buf)
	out_file.close()
	time.sleep(0.5)

