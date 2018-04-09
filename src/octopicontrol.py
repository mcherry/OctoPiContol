#!/usr/bin/python
# -*- coding: utf-8 -*-

# This script requires that libsdl be downgraded to version 1.2
# See here: https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/pitft-pygame-tips
# To calibrate touchscreen, use the following command: sudo TSLIB_FBDEVICE=/dev/fb1 TSLIB_TSDEVICE=/dev/input/touchscreen ts_calibrate
# Screen rotation can be adjusted using https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/adafruit-pitft.sh

import pygame
import os
import sys
import random
import socket
import fcntl
import struct
import json
import requests
from datetime import datetime
from pytz import timezone
from pygame.locals import *
from os.path import expanduser

# required environment variables for pygame
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

default_timezone = "US/Central";

home = expanduser("~")
with open(home + '/.octoprint_apikey', 'r') as apikey:
    dat_key = apikey.read().replace('\n', '')

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
    global dat_key
    
    headers = {
        'Content-Type': 'application/json',
	'X-Api-Key': dat_key
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

def createSurface(screen, bgcolor):
    bground = pygame.Surface(screen.get_size())
    bground = bground.convert()
    bground.fill(bgcolor)
		
    return bground

def backlightOff():
    file = open("/sys/class/backlight/soc:backlight/brightness","w") 
    file.write("0")
    file.close()
    return

def backlightOn():
    file = open("/sys/class/backlight/soc:backlight/brightness","w") 
    file.write("1")
    file.close()
    return

def printText(font, color, text, background, x, y):
    item = font.render(text, True, color)
    background.blit(item, (x, y))
    return

def Button1Pushed():
    return

def Button2Pushed():
    return

def main():
    global index
    global wclient
	
    runtime = 0
    ssaver_time = 5000
    screensaver_on = False
    return_from_ss = False
    api_version = "0"
    octo_version = "0"
    ext_target_f = "0"
    bed_target_f = "0"
    ds = u'\N{DEGREE SIGN}'
    is_paused = False
    pause_text = "Pause"

    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((480, 320))
    pygame.mouse.set_visible(False)
    
    Button1 = pygame.Rect(5, 152, 100, 100)
    Button2 = pygame.Rect(127, 152, 100, 100)
    Button3 = pygame.Rect(250, 152, 100, 100)
    Button4 = pygame.Rect(371, 152, 100, 100)
	
    # create font
    font = pygame.font.Font(get_script_path() + "/Fonts/NotoMono-Regular.ttf", 13)
	
    # main loop that shows and cycles time
    pos = (0, 0)
    clock = pygame.time.Clock()
    while True:
        clock.tick(25)
        
        for event in pygame.event.get():
            mouse_pos = pygame.mouse.get_pos()
            
            if event.type == QUIT:
                return
            
            elif event.type == MOUSEBUTTONDOWN:
                pygame.event.set_blocked(MOUSEBUTTONDOWN)
                                
                if Button1.collidepoint(mouse_pos):
                    if is_paused == False:
                        pause_text = "Resume"
                        is_paused = True
                    else:
                        pause_text = "Pause"
                        is_paused = False
                        
                    pygame.draw.rect(background, (255, 255, 255), Button1)
                    pauseText = font.render(pause_text, True, (0, 0, 0))
                    background.blit(pauseText, (35,192))
                    
                    Button1Pushed()

                if Button2.collidepoint(mouse_pos):
                    pygame.draw.rect(background, (255, 255, 255), Button2)
                    background.blit(font.render("Stop", True, (0, 0, 0)), (160,192))
                                
                if Button3.collidepoint(mouse_pos):
                    pygame.draw.rect(background, (255, 255, 255), Button3)
                    background.blit(font.render("Reboot", True, (0, 0, 0)), (275,192))
                    
                if Button4.collidepoint(mouse_pos):
                    pygame.draw.rect(background, (255, 255, 255), Button4)
                    background.blit(font.render("Power Off", True, (0, 0, 0)), (386,192))
                                    
                if return_from_ss != True:
                    runtime = 0
                    
                return_from_ss = False
                
                screen.blit(background, (0, 0))
                pygame.display.flip()
        
                break
            
            elif event.type == MOUSEBUTTONUP:
                if Button1.collidepoint(mouse_pos):
                    pygame.draw.rect(background, (255, 255, 255), Button1, 2)
                    background.blit(font.render(pause_text, True, (0, 0, 0)), (160,192))
                    
                if Button2.collidepoint(mouse_pos):
                    pygame.draw.rect(background, (255, 255, 255), Button2, 2)
                    background.blit(font.render("Stop", True, (0, 0, 0)), (160,192))
                    
                if Button3.collidepoint(mouse_pos):
                    pygame.draw.rect(background, (255, 255, 255), Button3, 2)
                    background.blit(font.render("Reboot", True, (0, 0, 0)), (275,192))
                    
                if Button4.collidepoint(mouse_pos):
                    pygame.draw.rect(background, (255, 255, 255), Button4, 2)
                    background.blit(font.render("Power Off", True, (0, 0, 0)), (386,192))
                
                #if is_paused == False:
                #    pause_text = "Resume"
                #    is_paused = True
                #else:
                #    pause_text = "Pause"
                #    is_paused = False
                
                #background.blit(font.render(pause_text, True, (255, 255, 255)), (35,192))
                #background.blit(font.render("Stop", True, (255, 255, 255)), (160,192))
                #background.blit(font.render("Reboot", True, (255, 255, 255)), (275,192))
                #background.blit(font.render("Power Off", True, (255, 255, 255)), (386,192))
                
                pygame.event.set_allowed(MOUSEBUTTONDOWN)
                
            screen.blit(background, (0, 0))
            pygame.display.flip()

	if screensaver_on is False:
            progress_completion = None
			
            job = get_info('job');
            if job is not None:
                status = job['state']
                file_name = job['job']['file']['name']
                file_size = job['job']['file']['size']
                progress_completion = job['progress']['completion']
                if progress_completion is not None: progress_completion = int(round(progress_completion));
                progress_printtimeleft = job['progress']['printTimeLeft']
            else:
                status = "Offline"
                file_name = "_.gcode"
                file_size = 0
                progress_completion = "0"
                progress_printtimeleft = "0"

				
            ver = get_info('version')
            if ver is not None:
                api_version = ver['api']
                octo_version = ver['server']
            else:
                api_version = 0
                octo_version = 0
            
            ext_f = "0"
            bed_f = "0"
			
            stateinfo = get_info('connection')
            if stateinfo is not None:
                state = stateinfo['current']['state']
            else:
                state = "Offline"
			
            printer = get_info('printer')
            if printer is not None:
                ext = int(printer['temperature']['tool0']['actual'])
                ext_target = int(printer['temperature']['tool0']['target'])
                bed = int(printer['temperature']['bed']['actual'])
                bed_target = int(printer['temperature']['bed']['target'])
            else:
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
		           
            # Fill background
            background = createSurface(screen, (0, 0, 0))
		
            # get time for currently selected timezone
            tzdata = datetime.now(timezone(default_timezone))
                    
            if ext_target_f == "32": ext_target_f = 0
            if bed_target_f == "32": bed_target_f = 0;
            if progress_printtimeleft is not None:
                time = float(int(progress_printtimeleft))
                day = time // (24 * 3600)
                time = time % (24 * 3600)
                hour = time // 3600
                time %= 3600
                minutes = time // 60
                time %= 60
            else:
                time = 0
                day = 0
                hour = 0
                minutes = 0
                    
            # render each string
            status_text = ""
            if progress_completion is not None:
                status_text = "Status: " + state + " (" + `progress_completion` + "%)"
            else:
                status_text = "Status:" + state

            filename_text = ""
            if file_name is not None:
                filename_text = "Name:   " + file_name.replace("_", " ").replace(".gcode", "")
            else:
                filename_text = "Name: "

            if file_size is not None:
                size_text = "Size:   " + "{:,}".format(file_size) + " Bytes"
            else:
                size_text = "Size:"
            
            ext_c = `ext`
            ext_target_c = `ext_target`
            bed_c = `bed`
            bed_target_c = `bed_target`
            
            bed_space = ""
            if len(bed_f) == 2:
                bed_space = " "
            
            printText(font, (255,255,255), status_text, background, 5,5)
            printText(font, (255,255,255), filename_text, background, 5,25)
            printText(font, (255,255,255), size_text, background, 5,45)
            printText(font, (255,255,255), "Ver: " + api_version + "-" + octo_version, background, 330,5)
            printText(font, (255,255,255), "  [ extruder: " + ext_f.rjust(3) + ds + "F / " + ext_c.rjust(3) + ds + "C  " + bed_space + "   bed:    " + bed_space + "   " + bed_f.rjust(3).replace(' ', '') + ds + "F / " + bed_c.rjust(3).replace(' ', '') + ds + "C ]", background, 5, 110)
            printText(font, (255,255,255), "  [ target:   " + ext_target_f.rjust(3) + ds + "F / " + ext_target_c.rjust(3) + ds + "C  " + bed_space + "   target:    " + bed_target_f.rjust(3).replace(' ', '') + ds + "F /" + bed_target_c.rjust(3) + ds + "C ]", background, 5, 128)
            printText(font, (255,255,255), "  [ wlan0: " + getIPAddr('wlan0').ljust(15) + "      mac: " + getHWAddr('wlan0').ljust(17) + " ]", background, 5,263)
            printText(font, (255,255,255), "  [ eth0:  " + getIPAddr('eth0').ljust(15) + "      mac: " + getHWAddr('eth0').ljust(17) + " ]", background, 5, 279)
            printText(font, (255,255,255), tzdata.strftime('%m-%d-%Y'), background, 5,300)
            printText(font, (255,255,255), "%02d:%02d:%02d" % (day, hour, minutes), background, 205, 300)
            printText(font, (255,255,255), tzdata.strftime('%H:%M:%S'), background, 405,300)
            
            setProgress(background, progress_completion)
    
            # buttons
            pygame.draw.rect(background, (255, 255, 255), Button1, 2)
            background.blit(font.render(pause_text, True, (255, 255, 255)), (35,192))
            
            pygame.draw.rect(background, (255, 255, 255), Button2, 2)
            background.blit(font.render("Stop", True, (255, 255, 255)), (160,192))
            
            pygame.draw.rect(background, (255, 255, 255), Button3, 2)
            background.blit(font.render("Reboot", True, (255, 255, 255)), (275,192))
            
            pygame.draw.rect(background, (255, 255, 255), Button4, 2)
            background.blit(font.render("Power Off", True, (255, 255, 255)), (386,192))
		
            screen.blit(background, (0, 0))
            pygame.display.flip()

            runtime += 1
			
            if runtime == ssaver_time:
                runtime = 0
                screensaver_on = True
        else:
            # fire up the screensaver
            size = [480,320]
			
            background = createSurface(screen, (0, 0, 0))
            screen.blit(background, (0, 0))
            pygame.display.flip()

            text_width = 13
            groups = []
            add_line = 1
            pos = random.randint(1, size[0] / text_width + 1) * text_width - text_width / 2

            while True:
                if screensaver_on is False:
                    break
									
		add_line -= 1
		if add_line == 0:
                    fast = random.randint(0,20)
                    if fast == 0:
                        speed = 3
                    else:
                        speed = random.randint(1,2)

                    add_line = 2
                    pos = random.randint(1, size[0] / text_width) * text_width - text_width / 2
                    groups.append(Group([pos, -font.get_height()], speed))
					
                if random.randint(0, 50) == 50:
                    matrixcode = ".: MP Mini Select V2 IIIP 3D Printer :."
                    code = list(matrixcode)
                    random.shuffle(code, random.random)
					
                    pos = [random.randint(1, size[0] / text_width + 1) * text_width-text_width / 2, random.randint(1, size[1] / font.get_height() + 1) * font.get_height()]
                    groups.append(CodePartical(pos, random.randint(0, len(code)-1), code))

                for group in groups:
                    group.modernize(font, size)
                    if group.dead:
                        groups.remove(group)
						
                rects = []
                            
                for group in groups:
                    for rect in group.render(screen, font):
                        rects.append(rect)

                pygame.display.flip()
                clock.tick(25)
				
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

