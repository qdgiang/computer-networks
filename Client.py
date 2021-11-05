from tkinter import *
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
from tkinter_custom_button import TkinterCustomButton

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	about_message = 'This is our submission for the Computer Networks Lab Assignment 1.\n\nOur group has three member:\n1. Quách Đằng Giang - 1952044\n2. Nguyễn Đức Thành - 1952983\n3. Lý Kim Phong - 1952916\n\n Have a great day 😎'

	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0


	def about_dialog(self):
		tkMessageBox.showinfo(title='About Us', message=self.about_message)

	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		"""
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=0, pady=0)
		"""
		
		# Create testing button for GUI improvment
		#self.setup = TkinterCustomButton(text="My Button", corner_radius=10, command=self.button_function)
		self.about= TkinterCustomButton(
                                            #bg_color='#4C566A',
                                            #fg_color='#4C566A',
                                            border_color="#ABB2B9",
                                            hover_color="#B48EAD",
                                            #text_font=None,
                                            text="About Us",
                                            text_color="white",
                                            corner_radius=150,
                                            #border_width=2,
                                            width=160,
                                            height=30,
                                            hover=True,
											text_font=("Helvetica", 15),
											text_when_hover='black',
                                            command=self.about_dialog)
		self.about.grid(row = 1, column = 4, padx = 2, pady = 2)

		self.setup= TkinterCustomButton(
                                            #bg_color='#4C566A',
                                            #fg_color='#4C566A',
                                            border_color="#ABB2B9",
                                            hover_color="#8FBCBB",
                                            #text_font=None,
                                            text="Setup",
                                            text_color="white",
                                            corner_radius=150,
                                            #border_width=2,
                                            width=160,
                                            height=30,
                                            hover=True,
											text_font=("Helvetica", 15),
											text_when_hover='black',
                                            command=self.setupMovie)
		self.setup.grid(row = 1, column = 0, padx = 2, pady = 2)

		self.start= TkinterCustomButton(
                                            #bg_color='#4C566A',
                                            #fg_color='#4C566A',
                                            border_color="#ABB2B9",
                                            hover_color="#5E81AC",
                                            #text_font=None,
                                            text="Play",
                                            text_color="white",
                                            corner_radius=150,
                                            #border_width=2,
                                            width=160,
                                            height=30,
                                            hover=True,
											text_font=("Helvetica", 15),
											text_when_hover='black',
                                            command=self.playMovie)
		self.start.grid(row = 1, column = 1, padx = 2, pady = 2)

		# Create Play button	
		"""
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		"""

		self.pause= TkinterCustomButton(
                                            #bg_color='#4C566A',
                                            #fg_color='#4C566A',
                                            border_color="#ABB2B9",
                                            hover_color="#EBCB8B",
                                            #text_font=None,
                                            text="Pause",
                                            text_color="white",
                                            corner_radius=150,
                                            #border_width=2,
                                            width=160,
                                            height=30,
                                            hover=True,
											text_font=("Helvetica", 15),
											text_when_hover='black',
                                            command=self.pauseMovie)
		self.pause.grid(row = 1, column = 2, padx = 2, pady = 2)

		"""
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		"""

		self.teardown= TkinterCustomButton(
                                            #bg_color='#4C566A',
                                            #fg_color='#4C566A',
                                            border_color="#ABB2B9",
                                            hover_color="#BF616A",
                                            #text_font=None,
                                            text="Teardown",
                                            text_color="white",
                                            corner_radius=150,
                                            #border_width=2,
                                            width=160,
                                            height=30,
                                            hover=True,
											text_font=("Helvetica", 15),
											text_when_hover='black',
                                            command=self.exitClient)
		self.teardown.grid(row = 1, column = 3, padx = 2, pady = 2)

		# Create Teardown button
		"""
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		"""
		# Create a label to display the movie
		self.label = Label(self.master, height=19, background = '#2E3440')
		self.label.grid(row=0, column=0, columnspan=5, sticky=W+E+N+S, padx=5, pady=5) 

	"""
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
"""
	def setupMovie(self):
		"""Setup button handler."""
	#TODO
	
	def exitClient(self):
		"""Teardown button handler."""
	#TODO

	def pauseMovie(self):
		"""Pause button handler."""
	#TODO
	
	def playMovie(self):
		"""Play button handler."""
	#TODO
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
	#TODO
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		
	
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		
		# Set the timeout value of the socket to 0.5sec
		# ...
		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
