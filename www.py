import tornado.ioloop
import tornado.web
import time
import sys
import os
from datetime import datetime
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import StringIO
import thread
import threading
import signal

class SlidingMessage(threading.Thread):
	message="LedPanel"
	stop_request_flag=False
	sliding_delay=0
	red=0
	green=0
	blue=1
	
	def if_stop_requested(self):
		return self.stop_request_flag

	def stop(self):
		self.stop_request_flag=True
		
	def set_message(self,message):
		self.message=message

	def set_color(self,red,green,blue):
		self.red=red
		self.green=green
		self.blue=blue

	def set_sliding_delay(self,sliding_delay):
		self.sliding_delay=sliding_delay
	
	def run(self):	
		font1 = ImageFont.truetype('fonts/Ubuntu-B.ttf',30)

		im = Image.new("RGB", (32, 32), "black")
		draw = ImageDraw.Draw(im)
		draw.fontmode="1" #No antialias
		width, height = font1.getsize(self.message)	
		
		out_file = open("/sys/class/ledpanel/rgb_buffer","w")
		output = StringIO.StringIO()

		if self.message=="":
			output.truncate(0)
			im.save(output, format='PPM')
			buf=output.getvalue()

			out_file.seek(0)
			out_file.write(buf[13:])
			out_file.close()

			while True:
				time.sleep(60)
		
		x = 32
		while True:
			x = x - 1

			if x < -(width):
				x = 32
				
			draw.rectangle((0, 0, 31, 31), outline=0, fill=0)

			if self.if_stop_requested():
				break;

			color_set=(self.red,self.green,self.blue)
			draw.text((x,-4), self.message, color_set, font=font1)

			output.truncate(0)
			im.save(output, format='PPM')
			buf=output.getvalue()

			out_file.seek(0)
			out_file.write(buf[13:])

			time.sleep(self.sliding_delay/100.0)

		out_file.close()
		return

def format_time():
    d = datetime.now()
    return "{:%H:%M}".format(d)

class set_color(tornado.web.RequestHandler):
	def get(self):
		red = int(self.get_argument("red", default="0"))
		green = int(self.get_argument("green", default="0"))
		blue = int(self.get_argument("blue", default="0"))
		t.set_color(red,green,blue)

class set_sliding_delay(tornado.web.RequestHandler):
	def get(self):
		sliding_delay = int(self.get_argument("delay", default="0"))
		t.set_sliding_delay(sliding_delay)
		
class send_message(tornado.web.RequestHandler):
	def get(self):
		global t
		message = self.get_argument("message", default="")
		t.set_message(message)

def signal_handler(signal, frame):
	global sliding_message

	print 'You pressed Ctrl+C!'
	t.stop()
	t.join()
	sys.exit(0)


application = tornado.web.Application([
	(r"/send_message", send_message),
	(r"/set_color", set_color),
	(r"/set_sliding_delay", set_sliding_delay),
	(r"/(.*)", tornado.web.StaticFileHandler, {"path": ".","default_filename": "index.html"}),
])

t=SlidingMessage()

if __name__ == "__main__":	
	t.start()
	
	signal.signal(signal.SIGINT, signal_handler)
	print 'Press Ctrl+C to exit'
	
	application.listen(80,"0.0.0.0")
	tornado.ioloop.IOLoop.instance().start() 
	

