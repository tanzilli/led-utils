import time
import random

buf=bytearray(32*32*3)

while True:
	i=0
	for row in range (0,32):
		for col in range (0,32):
				buf[i+0]=random.randint(0,7)<<5
				buf[i+1]=random.randint(0,7)<<5
				buf[i+2]=random.randint(0,7)<<5
				i=i+3

	out_file = open("/sys/class/ledpanel/rgb_buffer","w")
	out_file.write(buf)
	out_file.close()

