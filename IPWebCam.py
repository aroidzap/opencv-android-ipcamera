import cv2
import threading
import http.client
import asyncio
import websockets

class Audio():
	def __init__(self, ip = None, port = None):
		self.ip = ip
		self.port = port
	
	def send_file(self, wav_filename):
		with open(wav_filename, "rb") as file:
			self.send(file.read())

	def send(self, wav_data):
		async def send_audio(wav, ip, port):
			async with websockets.connect('ws://{}:{}/audioin.wav'.format(ip, port)) as ws:
				await ws.send(wav)
		asyncio.get_event_loop().run_until_complete(send_audio(wav_data, self.ip, self.port))

	def read(self):
		raise NotImplementedError("read not yet implemented")
		# 'http://{}:{}/audio.wav'.format(ip, port)

class Light:
	def __init__(self, ip = None, port = None):
		self.state = False
		if(ip is None or port is None):
			self.conn = None
		else:
			self.conn = http.client.HTTPConnection(ip, port)
	def on(self, enable = True):
		if(self.state != enable and self.conn is not None):
			if(enable):
				self.conn.request("GET", "/enabletorch")
				self.conn.getresponse()
			else:
				self.conn.request("GET", "/disabletorch")
				self.conn.getresponse()
			self.state = enable
	def off(self):
		self.on(False)

	def __exit__(self, exec_type, exc_value, traceback):
		self.conn.close()

class Video:
	def __init__(self, ip = None, port = None):
		if(ip is None or port is None):
			self.cap = cv2.VideoCapture(0)
		else:
			self.cap = cv2.VideoCapture("rtsp://{}:{}/h264_pcm.sdp".format(ip, port))

		_, self.frame = self.cap.read()
		self.run = True
		self.thread = threading.Thread(target=self.update, args=()).start()
		self.read_lock = threading.Lock()

	def update(self):
		while self.run:
			_, frame = self.cap.read()
			with self.read_lock:
				self.frame = frame

	def read(self):
		with self.read_lock:
			frame = None if self.frame is None else self.frame.copy()
		return frame

	def __exit__(self, exec_type, exc_value, traceback):
		self.run = False
		self.thread.join()
		self.cap.release()

if __name__ == "__main__":
	
	ip = "10.0.0.91"
	port = 8080
	
	audio = Audio(ip, port)
	light = Light(ip, port)
	video = Video(ip, port)

	sound = open('sound.wav', 'rb').read()

	frame = video.read()

	light.on()
	audio.send(sound)
	
	cv2.imshow('IP Camera', frame)
	cv2.waitKey()
	
	light.off()