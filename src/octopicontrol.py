#!/usr/bin/python
# -*- coding: utf-8 -*-

import pygame
import os
import sys
import time
import random
import socket
import fcntl
import struct
import json
import requests
from time import sleep
from datetime import datetime
from pytz import timezone
from pygame.locals import *

# required environment variables for pygame
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/event0')

default_timezone = "US/Central";

Button1 = pygame.Rect(5, 160, 100, 100)
Button2 = pygame.Rect(127, 160, 100, 100)
Button3 = pygame.Rect(250, 160, 100, 100)
Button4 = pygame.Rect(371, 160, 100, 100)

########## start screen saver classes ##########
#
# Matrix code borrowed and modified from Dylan J. Raub (dylanjraub)
# http://pygame.org/project-Matrix+code-756-.html

class CodePartical(object):
    def __init__(self, pos, frame, code):
        self.pos = [int(pos[0]),int(pos[1])]
        self.frame = int(frame)
        self.max_life = 30
        self.life = int(self.max_life)
        self.fade_time = 5
        self.code =  code
        self.dead = False

    def modernize(self, text, size):
        self.frame+=random.randint(1,3)/10.0
        if self.frame>=len(self.code):
            self.frame = 0

        self.life-=1
        if self.life<=0:
            self.dead = True
            
    def render(self, screen, text):
        if self.life>self.fade_time:
            color = [ 200*(float(self.life-self.fade_time)/(self.max_life-self.fade_time)) , 255 , 200*(float(self.life-self.fade_time)/(self.max_life-self.fade_time)) ]
        else:
            color = [ 0 , 255*(float(self.life)/self.fade_time) , 0 ]
            
        text_surface =  text.render(self.code[int(self.frame)], False, color)
        rect = text_surface.get_rect(center = self.pos)

        screen.blit(text_surface, rect)

        return [rect]

class Group(object): 
    def __init__(self, pos, speed):
		# "matrix code" is a string made up of the current timezone/time/date
		timedata = datetime.now(timezone(default_timezone))
		timestring = timedata.strftime('%X %Z %z') + default_timezone
		self.code = list(timestring)
		random.shuffle(self.code, random.random)
		
		self.speed=int(speed)
		self.pos =[  int(pos[0]),int(pos[1]) ]
		self.frame = 0
		self.update = 0
		self.particals = [CodePartical(self.pos, self.frame, self.code)]
		self.dead=False
        
    def modernize(self, text, size):
        self.update+=1
        if self.update==self.speed:
            self.update=0
            
            if self.pos[1]<size[1]:
                self.pos[1]+=text.get_height()
                self.particals.append(CodePartical(self.pos, int(self.frame), self.code))

            if len(self.particals)==0:
                self.dead = True           

        for partical in self.particals:
            partical.modernize(text, size)
            if partical.dead:
                self.particals.remove(partical)

        self.frame+=1
        if self.frame>=len(self.code):
            self.frame=0     

    def render(self, screen, text):
        rects = []
        
        for partical in self.particals:
            rects.append(  partical.render(screen, text)[0]  )

        return rects

class DelaySwitch(object):
    def __init__(self, frame_rate):
        # FRAME RATE IS IN FRAMES/SECOND
        self.frame_rate = 1.0/(frame_rate/100.0) # makes frame rate into milliseconds
        self.time = 0
        self.prev_time = 0
        self.time_passed = 0
    def update(self):
        self.time=time.time()
        self.time_passed = self.time-self.prev_time
        if self.time_passed>self.frame_rate:
            pass
        elif self.time_passed<self.frame_rate:
            time.sleep((self.frame_rate-self.time_passed)/100.0)
        self.prev_time = self.time

########## end screen saver classes ##########

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def getIPAddr(ifname):
    retval = ""
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        retval = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])
    except:
        retval = None
        
    if retval == None:
        return "000.000.000.000"
    else:
        return retval

def getHWAddr(ifname):
    retval = ""
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
        retval = ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]
    except:
        retval = None
    
    if retval == None:
        return "00:00:00:00:00:00"
    else:
        return retval

def headers():
	headers = {
		'Content-Type': 'application/json',
		'X-Api-Key': 'CDC8A137E67F454DB5CA45AEF6DE6973'
	}

	return headers
    

def get_info(api_path):
    response = requests.get("http://octopi.inditech.org/api/" + api_path, headers = headers())

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        return None

def put_info(api_path):
	response = requests.put("http://octopi.inditech.org/api/" + api_path, headers = headers())
	
	if response.status_code == 200:
		return json.loads(response.content.decode('utf-8'))
	else:
		return None

def CtoF(value):
	return `int(round(9 / 5 * value + 32))`

def rptstr(str, cnt):
	return ''.join([char * cnt for char in str])

def setProgress(surface, percent):
        pygame.draw.rect(surface, (255, 255, 255), (5, 65, 470, 40), 2)
        
	if percent >= 7:
		pygame.draw.rect(surface, (255, 255, 255), (14, 70, 30, 30))
	
	if percent >= 16:
		pygame.draw.rect(surface, (255, 255, 255), (49, 70, 30, 30))
	
	if percent >= 24:
		pygame.draw.rect(surface, (255, 255, 255), (84, 70, 30, 30))
	
	if percent >= 31:
		pygame.draw.rect(surface, (255, 255, 255), (119, 70, 30, 30))
	
	if percent >= 39:
		pygame.draw.rect(surface, (255, 255, 255), (154, 70, 30, 30))
	
	if percent >= 45:
		pygame.draw.rect(surface, (255, 255, 255), (189, 70, 30, 30))
	
	if percent >= 52:
		pygame.draw.rect(surface, (255, 255, 255), (224, 70, 30, 30))
	
	if percent >= 60:
		pygame.draw.rect(surface, (255, 255, 255), (260, 70, 30, 30))
	
	if percent >= 69:
		pygame.draw.rect(surface, (255, 255, 255), (295, 70, 30, 30))
	
	if percent >= 78:
		pygame.draw.rect(surface, (255, 255, 255), (330, 70, 30, 30))
	
	if percent >= 85:
		pygame.draw.rect(surface, (255, 255, 255), (365, 70, 30, 30))
	
	if percent >= 92:
		pygame.draw.rect(surface, (255, 255, 255), (401, 70, 30, 30))
	
	if percent >= 100:
		pygame.draw.rect(surface, (255, 255, 255), (437, 70, 30, 30))
        
        pygame.display.update(pygame.Rect(5, 65, 470, 40))

def createSurface(screen, bgcolor):
    bground = pygame.Surface(screen.get_size())
    bground = bground.convert()
    bground.fill(bgcolor)

    return bground

def draw_info_display(background, font):
    # render each string
    statusLabel = font.render("Status:", True, (255, 255, 255))
    fileLabel = font.render("Name:", True, (255, 255, 255))
    sizeLabel = font.render("Size:", True, (255, 255, 255))
    verLabel = font.render("Ver: ", True, (255, 255, 255))
    infoLine1 = font.render("               [ Ext:    F ]  [ Target:    F ]", True, (255, 255, 255))
    infoLine2 = font.render("               [ Bed:    F ]  [ Target:    D ]", True, (255, 255, 255))
    inetInfo2 = font.render("  [ wlan0:                 ]  [ mac:                   ]", True, (255, 255, 255))
    inetInfo1 = font.render("  [ eth0:                  ]  [ mac:                   ]", True, (255, 255, 255))

    background.blit(statusLabel, (5, 5))
    background.blit(fileLabel, (5, 25))
    background.blit(sizeLabel, (5, 45))
    background.blit(verLabel, (360, 45))
    background.blit(infoLine1, (2, 115))
    background.blit(infoLine2, (2, 135))
    background.blit(inetInfo1, (5,265))
    background.blit(inetInfo2, (5,280))
    
    # buttons
    pygame.draw.rect(background, (255, 255, 255), Button1, 2)
    pygame.draw.rect(background, (255, 255, 255), Button2, 2)
    pygame.draw.rect(background, (255, 255, 255), Button3, 2)
    pygame.draw.rect(background, (255, 255, 255), Button4, 2)
    
    #pygame.display.update(pygame.Rect(5, 5, 480, 75))
    #pygame.display.update(Button1)
    #pygame.display.update(Button2)
    #pygame.display.update(Button3)
    #pygame.display.update(Button4)

def draw_time_display(background, font, eta):
    tzdata = datetime.now(timezone(default_timezone))
    
    timeText = font.render(tzdata.strftime('%H:%M:%S'), True, (255, 255, 255))
    etaText = font.render(eta, True, (255, 255, 255))
    dateText = font.render(tzdata.strftime('%m-%d-%Y'), True, (255, 255, 255))
    
    background.blit(dateText, (5, 300))
    background.blit(etaText, (205, 300))
    background.blit(timeText, (405, 300))
    
    pygame.display.update(pygame.Rect(5, 300, 480, 320))
    
def main():
	global index
	global wclient
	
	runtime = 0
	ssaver_time = 720
	screensaver_on = False
	return_from_ss = False
	screenpressed = False
	ext_target_f = "0";
	bed_target_f = "0";
	
	# Initialise screen
	pygame.init()
	screen = pygame.display.set_mode((480, 320))
	pygame.mouse.set_visible(False)
	
	# create fonts
	font = pygame.font.Font(get_script_path() + "/Fonts/NotoMono-Regular.ttf", 13)
        
        background = createSurface(screen, (0, 0, 0))
        
        draw_info_display(background, font)
        screen.blit(background, (0, 0))
        pygame.display.flip()
	
	# main loop that shows and cycles time
	pos = (0, 0)
	while 1:
		for event in pygame.event.get():
			if event.type == QUIT:
				return
                        elif event.type == MOUSEBUTTONUP:
                                mouse_pos = pygame.mouse.get_pos()
                                
                                if Button1.collidepoint(mouse_pos):
                                    print "Pressed button 1"
                                    
                                if Button2.collidepoint(mouse_pos):
                                    print "Pressed button 2"
                                
                                if Button3.collidepoint(mouse_pos):
                                    print "Pressed button 3"
                                    
                                if Button4.collidepoint(mouse_pos):
                                    print "Pressed button 4"
                                    
                                if return_from_ss != True:
					runtime = 0
						
				return_from_ss = False
				break

		if screensaver_on is False:
			bad_read = False
			progress_completion = 0;
                        progress_printtimeleft = 0
                        file_name = rptstr(' ', 20)
                        file_size = 0
                        state = "Offline"
                        api_version = "0"
                        octo_version = "0"
                        
                        
			job = get_info('job');
			if job is not None:
				#status = job['state']
				file_name = job['job']['file']['name']
				file_size = job['job']['file']['size']
				progress_completion = job['progress']['completion']
				#progress_printtime = job['progress']['printTime']
				progress_printtimeleft = job['progress']['printTimeLeft']
			else:
				bad_read = True
				
			if progress_completion is None:
				progress_completion = 0
			else:
				progress_completion = int(round(progress_completion));
				
			ver = get_info('version')
			if ver is not None:
			    api_version = ver['api']
			    octo_version = ver['server']
			else:
			    bad_read = True
			
			ext_f = "0"
			bed_f = "0"
			
			stateinfo = get_info('connection')
			if stateinfo is not None:
				state = stateinfo['current']['state']
			else:
				bad_read = True
			
			printer = get_info('printer')
			if printer is not None:
				try:
					ext = int(printer['temperature']['tool0']['actual'])
					ext_target = int(printer['temperature']['tool0']['target'])
					bed = int(printer['temperature']['bed']['actual'])
					bed_target = int(printer['temperature']['bed']['target'])
				except:
					ext = 0
					ext_target = 0
					bed = 0
					bed_target = 0
					
				ext_f = CtoF(ext).ljust(3)
				bed_f = CtoF(bed).ljust(3)
				
				if ext_target == 0 or bed_target == 0:
					ext_target_f = "0".rjust(3)
					bed_target_f = "0".rjust(3)
				else:
					ext_target_f = CtoF(ext_target).ljust(3)
					bed_target_f = CtoF(bed_target).ljust(3)

			else:
				bad_read = True
				
			if file_name is None:
				file_name = rptstr(' ', 20);
				file_size = 0
				
			# Fill background
			#background = createSurface(screen, (0, 0, 0))
		
			# get time for currently selected timezone
			#tzdata = datetime.now(timezone(default_timezone))
			
			if ext_target_f == "32": ext_target_f = 0
			if bed_target_f == "32": bed_target_f = 0;
			
			if progress_printtimeleft is not None:
				time = float(int(progress_printtimeleft))
				day = time // (24 * 3600)
				time = time % (24 * 3600)
				hour = time // 3600
				time %= 3600
				minutes = time // 60
				#time %= 60
				#seconds = time
			else:
				time = 0
				day = 0
				hour = 0
				minutes = 0
				#seconds = 0
			
			eta = "%02d:%02d:%02d" % (day, hour, minutes)
			
			#setProgress(background, progress_completion);
			
			# render each string
			#statusLabel = font.render("Status: " + state + " (" + `progress_completion` + "%)", True, (255, 255, 255))
			#fileLabel = font.render("Name:   " + file_name.replace("_", " ").replace(".gcode", ""), True, (255, 255, 255))
			#sizeLabel = font.render("Size:   " + "{:,}".format(file_size) + " Bytes", True, (255, 255, 255))
			#verLabel = font.render("Ver: " + api_version + "-" + octo_version, True, (255, 255, 255))
			#infoLine1 = font.render("               [ Ext: " + ext_f + "F ]  [ Target: " + ext_target_f + "F ]", True, (255, 255, 255))
			#infoLine2 = font.render("               [ Bed: " + bed_f + "F ]  [ Target: " + bed_target_f + "F ]", True, (255, 255, 255))
			#inetInfo2 = font.render("  [ wlan0: " + getIPAddr('wlan0').ljust(15) + " ]  [ mac: " + getHWAddr('wlan0').ljust(17) + " ]", True, (255, 255, 255))
			#inetInfo1 = font.render("  [ eth0:  " + getIPAddr('eth0').ljust(15) + " ]  [ mac: " + getHWAddr('eth0').ljust(17) + " ]", True, (255, 255, 255))
			#timeText = font.render(tzdata.strftime('%H:%M:%S'), True, (255, 255, 255))
			#etaText = font.render(eta, True, (255, 255, 255))
			#dateText = font.render(tzdata.strftime('%m-%d-%Y'), True, (255, 255, 255))

			#background.blit(statusLabel, (5, 5))
			#background.blit(fileLabel, (5, 25))
			#background.blit(sizeLabel, (5, 45))
			#background.blit(verLabel, (360, 45))
                        
			# progress bar
			#pygame.draw.rect(background, (255, 255, 255), (5, 65, 470, 40), 2)
			
			#background.blit(infoLine1, (2, 115))
			#background.blit(infoLine2, (2, 135))
			
			# buttons
			#pygame.draw.rect(background, (255, 255, 255), Button1, 2)
			#pygame.draw.rect(background, (255, 255, 255), Button2, 2)
			#pygame.draw.rect(background, (255, 255, 255), Button3, 2)
			#pygame.draw.rect(background, (255, 255, 255), Button4, 2)
			
			#background.blit(inetInfo1, (5,265))
			#background.blit(inetInfo2, (5,280))
			
			# date and time
			#background.blit(dateText, (5, 300))
			#background.blit(etaText, (205, 300))
			#background.blit(timeText, (405, 300))
			
			#screen.blit(background, (0, 0))
			#pygame.display.flip()
                        draw_time_display(background, font, eta)
			
			# wait a second to refresh
			runtime += 1
			
			if runtime == ssaver_time:
				runtime = 0
				screensaver_on = True
				
			sleep(0.25)
                        pygame.time.Clock().tick(25)
		
		else:
			# fire up the screensaver
			size = [480,320]
			
			background = createSurface(screen, (0, 0, 0))
			screen.blit(background, (0, 0))
			#delay = DelaySwitch(25)

			text_width = 13
			groups = []

			add_line=1
			pos = random.randint(1,size[0]/text_width+1)*text_width-text_width/2

			while True:
				if screensaver_on is False:
					break
									
				add_line-=1
				if add_line==0:
					fast = random.randint(0,20)
					if fast==0:
						speed = 3
					else:
						speed = random.randint(1,2)

					add_line=2
					pos = random.randint(1,size[0]/text_width)*text_width-text_width/2
					groups.append(Group([pos, -font.get_height()], speed))
					
				if random.randint(0,50) == 50:
					matrixcode = "MP Mini Slect V2 IIIP 3D Printer"
					code = list(matrixcode)
					random.shuffle(code, random.random)
					
					pos = [random.randint(1,size[0]/text_width+1)*text_width-text_width/2, random.randint(1,size[1]/font.get_height()+1)*font.get_height()]
					groups.append(CodePartical(pos, random.randint(0,len(code)-1), code))


				for group in groups:
					group.modernize(font, size)
					if group.dead:
						groups.remove(group)
						
				rects = []
				for group in groups:
					for rect in group.render(screen, font):
						rects.append(rect)
						
				#delay.update()
				
				pygame.display.flip()
				pygame.time.Clock().tick(25)
				
				for rect in rects:
					screen.fill([0,0,0], rect)

				for event in pygame.event.get():
					if event.type is MOUSEBUTTONUP:
						screensaver_on = False
						return_from_ss = True
						
						break
											
					elif event.type == QUIT:
						return


if __name__ == '__main__': main()
