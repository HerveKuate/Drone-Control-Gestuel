#!/usr/bin/python

import threading
import time
import cv2
import numpy as np
import time
import io
import picamera
import socket
import struct
import subprocess as sp
from decimal import *

import sys

import navio.pwm
import navio.util
import datetime

navio.util.check_apm()

PWM_OUTPUT = 0
PWM_OUTPUT2 = 2
PWM_OUTPUT3 = 4
PWM_OUTPUT4 = 6

SERVO_MIN = 1.000  #ms
SERVO_MAX = 2.000  #ms
SERVO_NOM = 1.600  #ms
SERVO_STATUS = "stopped"
SERVO_STATUS2 = False
SERVO_SPEED = 1.400

def loop_for(seconds, *args):
	endtime = datetime.datetime.now() + datetime.timedelta(seconds=seconds)

	while True:
		if datetime.datetime.now() >= endtime:
			break
		pwm.set_duty_cycle(*args)
		pwm2.set_duty_cycle(*args)
		pwm3.set_duty_cycle(*args)
		pwm4.set_duty_cycle(*args)

def calibration():
	print "******Esc calibration********"
	loop_for(3, SERVO_MAX)
	loop_for(5, SERVO_MIN)
	loop_for(3, SERVO_MIN)
	loop_for(1, SERVO_NOM)  #3 before
	print "******Done********"

def stop(): #This will stop every action your Pi is performing for ESC ofcourse.
	pwm.set_duty_cycle(0)
	pwm2.set_duty_cycle(0)
	pwm3.set_duty_cycle(0)
	pwm4.set_duty_cycle(0)

def speed(x):	
	pwm.set_duty_cycle(x)
	pwm2.set_duty_cycle(x)
	pwm3.set_duty_cycle(x)
	pwm4.set_duty_cycle(x)
	
# Define a function for the thread
def servo():
	global SERVO_STATUS
	global SERVO_SPEED
	while True:
		if SERVO_STATUS == "stop":
			stop()
			SERVO_STATUS = "stopped"
			
		if SERVO_STATUS == "demarrage":
			calibration()
			SERVO_STATUS = "speed"
			
		if SERVO_STATUS == "speed":
			speed(SERVO_SPEED)
			
		if SERVO_STATUS == "stopped":
			time.sleep(0.2)
			#pass
			
		if SERVO_STATUS == "exit":
			break
#Spower = Decimal((1300.000 + (a * 700.000 / 640.000))/1000.000)
#Spower = round(Spower, 3)
#print Spower


pwm = navio.pwm.PWM(PWM_OUTPUT)
pwm2 = navio.pwm.PWM(PWM_OUTPUT2)
pwm3 = navio.pwm.PWM(PWM_OUTPUT3)
pwm4 = navio.pwm.PWM(PWM_OUTPUT4)

pwm.initialize()
pwm2.initialize()
pwm3.initialize()
pwm4.initialize()

pwm.set_period(50)
pwm2.set_period(50)
pwm3.set_period(50)
pwm4.set_period(50)

pwm.enable()
pwm2.enable()
pwm3.enable()
pwm4.enable()

t1 = threading.Thread(target=servo, args=[])
t1.start()

stream = io.BytesIO()

print "*****Command*****"
print "demarrage = 1 palm (pomme de la main)"
print "arret = 1 fists"
print "acceleration = 2 palm"
print "decceleration = 2 fist"
print "photo = palm when drone is ON"
print ""


with picamera.PiCamera() as camera:
	camera.resolution = (640, 480)
	camera.start_preview()
	time.sleep(2)

	try:
		for filename in camera.capture_continuous(stream, format='jpeg'):
			stream.truncate()
			stream.seek(0) 
			buff = np.fromstring(stream.getvalue(), dtype=np.uint8)
			time.sleep(0.5)
			image = cv2.imdecode(buff, 1)
			gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
			
			hand_cascade = cv2.CascadeClassifier('/mnt/usbdrive/Navio2/Python/hand.xml')
			fist_cascade = cv2.CascadeClassifier('/mnt/usbdrive/Navio2/Python/fist_v3.xml')
			left_cascade = cv2.CascadeClassifier('/mnt/usbdrive/Navio2/Python/left.xml')
			lpalm_cascade = cv2.CascadeClassifier('/mnt/usbdrive/Navio2/Python/lpalm.xml')
			right_cascade = cv2.CascadeClassifier('/mnt/usbdrive/Navio2/Python/right.xml')
			rpalm_cascade = cv2.CascadeClassifier('/mnt/usbdrive/Navio2/Python/rpalm.xml')
			palm_cascade = cv2.CascadeClassifier('/mnt/usbdrive/Navio2/Python/palm_v4.xml')
			
			#hands = hand_cascade.detectMultiScale(gray, 1.1, 7)
			palm = palm_cascade.detectMultiScale(gray, 1.1, 7)
			fist = fist_cascade.detectMultiScale(gray, 1.1, 7)
			#left = left_cascade.detectMultiScale(gray, 1.1, 7)
			#lpalm = lpalm_cascade.detectMultiScale(gray, 1.1, 7)
			#right = right_cascade.detectMultiScale(gray, 1.1, 7)
			#rpalm = rpalm_cascade.detectMultiScale(gray, 1.1, 7)  #2 before
			
			if len(fist) == 1 : #arret
				print "Found "+str(len(fist))+" fist"
				if SERVO_STATUS2:
					print "*****arret*****"
					SERVO_STATUS2 = False
					SERVO_STATUS = "stop"
			
			if len(palm) == 1 : #demarrage
				print "Found "+str(len(palm))+" palm(s)"
				if not SERVO_STATUS2:
					print "*****demarage*****"
					SERVO_STATUS2 = True
					SERVO_STATUS = "demarrage"
				else:
					print "*****prise photo*****"
					cv2.imwrite('resultcv.jpg',image)		
			
			if len(fist) == 2 :
				if SERVO_STATUS2:
					if SERVO_SPEED > 1.300:
						print "-1 speed"
						SERVO_SPEED -= 0.100
					else:
						print "speed minimun reached"
						
			if len(palm) == 2 :
				if SERVO_STATUS2:
					if SERVO_SPEED < 1.700:
						print "+1 speed"
						SERVO_SPEED += 0.100
					else:
						print "speed maximun reached"
			
			# if len(lpalm) > 0 or len(left) > 0: #speed  down
				# print "Found "+str(len(lpalm))+" lpalm(s)"+str(len(left))+" left"
				# if SERVO_STATUS2:
					# if SERVO_SPEED > 1.300:
						# print "-1 speed"
						# SERVO_SPEED -= 0.100
					# else:
						# print "speed minimun reached"
					
			# if len(rpalm) > 0 or len(right) > 0: #speed  up
				# print "Found "+str(len(rpalm))+" rpalm(s)"+str(len(right))+" right"
				# if SERVO_STATUS2:
					# if SERVO_SPEED < 1.700:
						# print "+1 speed"
						# SERVO_SPEED += 0.100
					# else:
						# print "speed maximun reached"
						
	except KeyboardInterrupt:
		print "attempting to close thread"
		SERVO_STATUS = "exit"
		t1.join()
		print "thread successfully closed"




