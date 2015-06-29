#!/usr/bin/python
# Send all 0 to the ledpanel

buf=bytearray(32*32*3)
out_file = open("/sys/class/ledpanel/rgb_buffer","w")
out_file.write(buf)
out_file.close()
