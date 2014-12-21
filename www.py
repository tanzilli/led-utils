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
sliding_delay=14	# keep in sync with index.html
red=1<<5
green=1<<5
blue=1<<5
baseline=-1	# vertical text position: -5=top, +4=bottom(no descenders)

class SlidingMessage(threading.Thread):
	message="Vuoto"
	stop_request_flag=False
	invalidate_cache_request_flag=False
	cache = []
	
	def __init__(self,message):
		threading.Thread.__init__(self)
		self.message=message
		return

	def ifStopRequested(self):
		return self.stop_request_flag

	def stop(self):
		self.stop_request_flag=True

	def invalidateCache(self):
		self.invalidate_cache_request_flag=True

	def run(self):
		global red,green,blue
		global sliding_delay

		font1 = ImageFont.truetype('Ubuntu-B.ttf',30)

		im = Image.new("RGB", (32, 32), "black")		# The 'off' color
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

		self.invalidate_cache_request_flag = True
		cache_idx = 0
		x = 32
		while not self.ifStopRequested():
			x = x - 1

			if x < -(width):
				x = 32
				cache_idx = 0

			if self.invalidate_cache_request_flag:
				self.invalidate_cache_request_flag = False
				self.cache = [ None for i in range(32 + width + 1) ]

			if self.cache[cache_idx] is None:
				bgcol=(0<<5,0<<5,0<<5)
				draw.rectangle((0, 0, 31, 31), outline=bgcol, fill=bgcol)	# Background color

				color_set=(red,green,blue)
				draw.text((x,baseline), self.message, color_set, font=font1)

				output.truncate(0)
				im.save(output, format='PPM')
				buf=output.getvalue()
				self.cache[cache_idx] = buf[13:]

			out_file.seek(0)
			out_file.write(self.cache[cache_idx])

			time.sleep(sliding_delay/1000.0)
			cache_idx = cache_idx + 1

		out_file.close()
		return

def format_time():
    d = datetime.now()
    return "{:%H:%M}".format(d)

class set_color(tornado.web.RequestHandler):
	def get(self):
		global red,green,blue
		red = int(self.get_argument("red", default="0"))<<5
		green = int(self.get_argument("green", default="0"))<<5
		blue = int(self.get_argument("blue", default="0"))<<5

		global sliding_message
		sliding_message.invalidateCache()

class set_sliding_delay(tornado.web.RequestHandler):
	def get(self):
		global sliding_delay
		sliding_delay = int(self.get_argument("delay", default="0"))

class send_message(tornado.web.RequestHandler):
	def get(self):
		global sliding_message

		message = self.get_argument("message", default="")

		## What is this?
		# self.write(message)
		
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
        sliding_message=SlidingMessage(" Welcome ")	# keep in sync with index.html
        sliding_message.start()
	application.listen(8000,"0.0.0.0")
	tornado.ioloop.IOLoop.instance().start() 

