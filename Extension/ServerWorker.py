import random, math
import time
from random import randint
import sys, traceback, threading, socket
import os
from VideoStream import VideoStream
from RtpPacket import RtpPacket

class ServerWorker:
#request
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'
	EXIT = 'EXIT'
	DESCRIBE= 'DESCRIBE'
	FORWARD = 'FORWARD'
	BACKWARD = 'BACKWARD'
#state
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	backward = 0
	forward = 0

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2

	clientInfo = {}

	def __init__(self, clientInfo):
		self.clientInfo = clientInfo

	def run(self):
		threading.Thread(target=self.recvRtspRequest).start()

	def recvRtspRequest(self):
		"""Receive RTSP request from the client."""
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:
			data = connSocket.recv(256)  ###
			if data:
				print ('*'*40 + "\nData received:\n" + '*'*40)
				self.processRtspRequest(data)

	def processRtspRequest(self, data):
		"""Process RTSP request sent from the client."""
		# Get the request type
		request = data.decode().split('\n')
		print('RTSP from client:',request)
		line1 = request[0].split(' ')
		requestType = line1[0]
		# Get the media file name
		filename = line1[1]
		# Get the RTSP sequence number
		seq = request[1].split(' ')

		# Process SETUP request
		if requestType == self.SETUP:
			if self.state == self.INIT:
				# Update state
				print ("SETUP Request received\n")
				try:
					self.clientInfo['videoStream'] = VideoStream(filename)
					self.state = self.READY
					self.clientInfo['videoStream'].calTotalTime()  # calculate length of video in second
					self.totalTime = self.clientInfo['videoStream'].totalTime # length of video in second
					self.fps = self.clientInfo['videoStream'].fps # fps of video
					self.noFrames = self.clientInfo['videoStream'].numFrame # Number of frames of video
					self.clientInfo['videoStream'].getPosFrame() # make position list of each frame in file
				except IOError:
					self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
				# Generate a randomized RTSP session ID
				self.clientInfo['session'] = randint(100000, 999999)
				# Send RTSP reply
				self.replyRtsp(self.OK_200, seq[1])  #seq[0] the sequenceNum received from Client.py
				print ("Sequence Number: " + seq[1])
				# Get the RTP/UDP port from the last line
				self.clientInfo['rtpPort'] = request[2].split(' ')[3]
				print ('*'*40 + "\nRTPPort is: " + self.clientInfo['rtpPort'] + "\n" + '*'*40)
				print ("Filename: " + filename)

		# Process PLAY request
		elif requestType == self.PLAY:
			if self.state == self.READY:
				print ('*'*40 + "\nPLAY Request Received\n" + '*'*40)
				self.state = self.PLAYING

				# Create a new socket for RTP/UDP
				self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

				self.replyRtsp(self.OK_200, seq[1])
				print ('*'*40 + "\nSequence Number ("+ seq[1] + ")\nReplied to client\n" + '*'*40)

				# Create a new thread and start sending RTP packets
				self.clientInfo['event'] = threading.Event()
				self.clientInfo['worker']= threading.Thread(target=self.sendRtp)
				self.clientInfo['worker'].start()
			# Process RESUME request !!!No pause state
			elif self.state == self.PAUSE:
				print ('*'*40 + "\nRESUME Request Received\n" + '*'*40)
				self.state = self.PLAYING

		# Process PAUSE request
		elif requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print ('*'*40 + "\nPAUSE Request Received\n" + '*'*40)
				self.state = self.READY

				self.clientInfo['event'].set()

				self.replyRtsp(self.OK_200, seq[1])

		# Process TEARDOWN request
		elif requestType == self.TEARDOWN:
			print ('*'*40 + "\nTEARDOWN Request Received\n" + '*'*40)
			self.state = self.READY
			self.clientInfo['event'].set()
			self.clientInfo['videoStream'].reset_frame()
			self.replyRtsp(self.OK_200, seq[1])

		# Process EXIT request
		elif requestType == self.EXIT:
			print ('*'*40 + "\nEXIT Request Received\n" + '*'*40)

			self.clientInfo['event'].set()

			self.replyRtsp(self.OK_200, seq[1])

			# Close the RTP socket
			self.clientInfo['rtpSocket'].close()
		# Process DESCRIBE request
		elif requestType == self.DESCRIBE:
			print ('*'*40 + "\nDESCRIBE Request Received\n" + '*'*40)
			self.replyRtsp(self.OK_200, seq[1])

		# Process FORWARD request
		elif requestType == self.FORWARD:
			if self.state == self.PLAYING:
				print ('*'*40 + "\nFORWARD Request Received\n" + '*'*40)
				self.replyRtsp(self.OK_200, seq[1])
				self.forward=1
			else:
				print('The video is not pause!!')
		# Process BACKWARD request
		elif requestType == self.BACKWARD:
			if self.state == self.PLAYING:
				print ('*'*40 + "\nBACKWARD Request Received\n" + '*'*40)
				self.replyRtsp(self.OK_200, seq[1])
				self.backward=1
			else:
				print('The video is not pause!!')

	def sendRtp(self):
		"""Send RTP packets over UDP."""

		counter = 0
		threshold = 10
		while True:
			self.clientInfo['event'].wait(0.05)

			# Stop sending if request is PAUSE or TEARDOWN
			if self.clientInfo['event'].isSet():
				break

			data = self.clientInfo['videoStream'].nextFrame(self.forward,self.backward)
			#print '*'*40 + "\ndata from nextFrame():\n" + data + "\n"
			if data:
				frameNumber = self.clientInfo['videoStream'].frameNbr()
				try:
					address = self.clientInfo['rtspSocket'][1][0]
					port = int(self.clientInfo['rtpPort'])
					self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port))
				except:
					print ("Connection Error")
					print ('*'*40)
					traceback.print_exc(file=sys.stdout)
					print ('*'*40)
			else:
				try:
					address = self.clientInfo['rtspSocket'][1][0]
					port = int(self.clientInfo['rtpPort'])
					self.clientInfo['rtpSocket'].sendto(self.makeRtp(bytearray(1),0 ),(address,port))
					#self.clientInfo['event'].set()
					print('Stop sending RTP to client')
					#self.clientInfo['videoStream'].reset_frame()

				except:
					print ("Connection Error")
					print ('*'*40)
					traceback.print_exc(file=sys.stdout)
					print ('*'*40)
			if self.backward==1: self.backward = 0
			if self.forward==1: self.forward = 0


	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0
		rtpPacket = RtpPacket()

		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)

		return rtpPacket.getPacket()

	def replyRtsp(self, code, seq):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print "200 OK"
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			#add info
			reply += "\nCurrFrame: %s" % self.clientInfo['videoStream'].frameNbr()
			reply += "\nVidLen: %s" % str(self.clientInfo['videoStream'].totalTime)
			reply += "\nFPS: %s" % str(self.fps)
			reply += "\nFrames: %s" % str(self.noFrames)
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			print ("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print ("500 CONNECTION ERROR")
