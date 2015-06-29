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

sliding_message=None
sliding_delay=0
red=1
green=1
blue=1

class SlidingMessage(threading.Thread):
	message="Vuoto"
	stop_request_flag=False
	
	def __init__(self,message):
		threading.Thread.__init__(self)
		self.message=message
		return

	def ifStopRequested(self):
		return self.stop_request_flag

	def stop(self):
		self.stop_request_flag=True
		
	def run(self):	
		global red,green,blue
		global sliding_delay
		
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

			if self.ifStopRequested():
				break;

			color_set=(red,green,blue)
			draw.text((x,-4), self.message, color_set, font=font1)

			output.truncate(0)
			im.save(output, format='PPM')
			buf=output.getvalue()

			out_file.seek(0)
			out_file.write(buf[13:])

			time.sleep(sliding_delay/100.0)

		out_file.close()
		return

def format_time():
    d = datetime.now()
    return "{:%H:%M}".format(d)

class set_color(tornado.web.RequestHandler):
	def get(self):
		global red,green,blue
		red = int(self.get_argument("red", default="0"))
		green = int(self.get_argument("green", default="0"))
		blue = int(self.get_argument("blue", default="0"))

class set_sliding_delay(tornado.web.RequestHandler):
	def get(self):
		global sliding_delay
		sliding_delay = int(self.get_argument("delay", default="0"))

class send_message(tornado.web.RequestHandler):
	def get(self):
		global sliding_message

		message = self.get_argument("message", default="")

		self.write(message)
		
		if sliding_message!=None:
			sliding_message.stop()
		
		sliding_message=SlidingMessage(message)
		sliding_message.start()

application = tornado.web.Application([
	(r"/send_message", send_message),
	(r"/set_color", set_color),
	(r"/set_sliding_delay", set_sliding_delay),
	(r"/(.*)", tornado.web.StaticFileHandler, {"path": ".","default_filename": "index.html"}),
])

if __name__ == "__main__":
	application.listen(80,"0.0.0.0")
	tornado.ioloop.IOLoop.instance().start() 
	

