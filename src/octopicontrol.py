#!/usr/bin/python
# -*- coding: utf-8 -*-

# This script requires that libsdl be downgraded to version 1.2
# See here: https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/pitft-pygame-tips
# To calibrate touchscreen, use the following command: sudo TSLIB_FBDEVICE=/dev/fb1 TSLIB_TSDEVICE=/dev/input/touchscreen ts_calibrate
# Screen rotation can be adjusted using https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/adafruit-pitft.sh

import fcntl
import json
import os
import pygame
import random
import requests
import signal
import socket
import struct
import sys
import time
from datetime import datetime
from os.path import expanduser
from pytz import timezone
from pygame.locals import *

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
            color = [ 0*(float(self.life-self.fade_time)/(self.max_life-self.fade_time)) , 0 , 255*(float(self.life-self.fade_time)/(self.max_life-self.fade_time)) ]
        else:
            color = [ 100 , 100*(float(self.life)/self.fade_time) , 255 ]
            
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

def ctrl_c(signal, frame):
    pygame.quit() 

def get_info(api_path):
    response = requests.get("http://octopi.inditech.org/api/" + api_path, headers = headers())

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        return None

def post_info(api_path, command):
    response = requests.post("http://octopi.inditech.org/api/" + api_path, headers = headers(), data = json.dumps(command))
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
	return None

def CtoF(value):
    return `int(round(9 / 5 * value + 32))`

def rptstr(str, cnt):
    return ''.join([char * cnt for char in str])

def setProgress(surface, percent):
    WHITE = (255,255,255)
    pygame.draw.rect(surface, WHITE, (5, 65, 470, 40), 2)
    
    if percent >= 7:
        pygame.draw.rect(surface, WHITE, (14, 70, 30, 30))
    if percent >= 16:
	pygame.draw.rect(surface, WHITE, (49, 70, 30, 30))
    if percent >= 24:
	pygame.draw.rect(surface, WHITE, (84, 70, 30, 30))
    if percent >= 31:
	pygame.draw.rect(surface, WHITE, (119, 70, 30, 30))
    if percent >= 39:
	pygame.draw.rect(surface, WHITE, (154, 70, 30, 30))
    if percent >= 45:
	pygame.draw.rect(surface, WHITE, (189, 70, 30, 30))
    if percent >= 52:
        pygame.draw.rect(surface, WHITE, (224, 70, 30, 30))
    if percent >= 60:
        pygame.draw.rect(surface, WHITE, (260, 70, 30, 30))
    if percent >= 69:
	pygame.draw.rect(surface, WHITE, (295, 70, 30, 30))
    if percent >= 78:
	pygame.draw.rect(surface, WHITE, (330, 70, 30, 30))
    if percent >= 85:
	pygame.draw.rect(surface, WHITE, (365, 70, 30, 30))
    if percent >= 92:
	pygame.draw.rect(surface, WHITE, (401, 70, 30, 30))
    if percent >= 100:
	pygame.draw.rect(surface, WHITE, (437, 70, 30, 30))

def createSurface(screen, bgcolor):
    bground = pygame.Surface(screen.get_size())
    bground = bground.convert()
    bground.fill(bgcolor)
		
    return bground

def backLight(state):
    file = open("/sys/class/backlight/soc:backlight/brightness","w") 
    file.write(state)
    file.close()
    return

def printText(font, color, text, background, x, y):
    item = font.render(text, True, color)
    background.blit(item, (x, y))
    return

def confirm(screen, message):
    return_val = False
    button_clicked = False
    
    WHITE = (255,255,255)
    BLACK = (0,0,0)
    
    Button1 = pygame.Rect(160, 235, 150, 75)
    Button2 = pygame.Rect(320, 235, 150, 75)
    font = pygame.font.Font(get_script_path() + "/Fonts/NotoMono-Regular.ttf", 15)
    background = createSurface(screen, BLACK)
    
    printText(font, WHITE, message, background, 5,5)
    pygame.draw.rect(background, WHITE, Button1, 2)
    background.blit(font.render("Yes", True, WHITE), (215,270))
            
    pygame.draw.rect(background, WHITE, Button2, 2)
    background.blit(font.render("No", True, WHITE), (395,270))

    screen.blit(background, (0, 0))
    pygame.display.flip()
    
    clock = pygame.time.Clock()
    while True:
        clock.tick(15)
        
        for event in pygame.event.get():
            mouse_pos = pygame.mouse.get_pos()
            
            if event.type == QUIT:
                return
            
            elif event.type == MOUSEBUTTONDOWN:
                pygame.event.set_blocked(MOUSEBUTTONDOWN)
                
                #if Button1.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button3)
                #    background.blit(font.render("Yes", True, BLACK), (275,192))
                #    
                #if Button2.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button4)
                #    background.blit(font.render("No", True, BLACK), (386,192))
                    
            elif event.type == MOUSEBUTTONUP:
		pygame.event.set_allowed(MOUSEBUTTONDOWN)
                #if Button1.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button1, 2)
                #    background.blit(font.render("Yes", True, BLACK), (35,192))
                #    return_val = True
                #    button_clicked = True
                #    
                #if Button2.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button2, 2)
                #    background.blit(font.render("No", True, BLACK), (152,192))
                #    return_val = False
                #    button_clicked = True
            
            if button_clicked == True:
                return return_val

def main():
    global index
    global wclient
    
    WHITE = (255,255,255)
    BLACK = (0,0,0)
	
    runtime = 0
    ssaver_time = 720
    screensaver_on = False
    return_from_ss = False
    api_version = "0"
    octo_version = "0"
    ext_target_f = "0"
    bed_target_f = "0"
    ds = u'\N{DEGREE SIGN}'
    is_paused = False
    pause_text = "Pause"

    signal.signal(signal.SIGINT, ctrl_c)

    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((320, 480))
    pygame.mouse.set_visible(False)
    
    #Button1 = pygame.Rect(5, 152, 100, 100)
    #Button2 = pygame.Rect(127, 152, 100, 100)
    #Button3 = pygame.Rect(250, 152, 100, 100)
    #Button4 = pygame.Rect(371, 152, 100, 100)
	
    # create font
    font = pygame.font.Font(get_script_path() + "/Fonts/NotoMono-Regular.ttf", 15)
	
    # main loop that shows and cycles time
    pos = (0, 0)
    clock = pygame.time.Clock()
    while True:
        clock.tick(15)
        
        for event in pygame.event.get():
            mouse_pos = pygame.mouse.get_pos()
            
            if event.type == QUIT:
                return
            
            elif event.type == MOUSEBUTTONDOWN:
                pygame.event.set_blocked(MOUSEBUTTONDOWN)
                                
                #if Button1.collidepoint(mouse_pos):
                #    if is_paused == False:
                #        post_info("job", {'command': 'pause', 'action': 'pause'})
                #        pause_text = "Resume"
                #        is_paused = True
                #    else:
                #        post_info('job', {'command': 'pause', 'action': 'resume'})
                #        pause_text = "Pause"
                #        is_paused = False
                #        
                #    pygame.draw.rect(background, WHITE, Button1)
                #    pauseText = font.render(pause_text, True, BLACK)
                #    background.blit(pauseText, (35,192))

                #if Button2.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button2)
                #    background.blit(font.render("Cancel", True, BLACK), (152,192))
                #    
                #    cancel = confirm(background, "Are you sure you want to cancel the current job?")
                #    if cancel == True:
                #        post_info('job', {'command': 'cancel'})
                                
                #if Button3.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button3)
                #    background.blit(font.render("Reboot", True, BLACK), (275,192))
                #    
                #    check = confirm(screen, "Are you sure you want to reboot?")
                #    if check == True:
                #        backLight("0")
                #        os.system("/sbin/reboot")
                    
                #if Button4.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button4)
                #    background.blit(font.render("Power Off", True, BLACK), (386,192))
                #    check = confirm(screen, "Are you sure you want to power off?")
                #    if check == True:
                #        backLight("0")
                #        os.system("/sbin/poweroff")
                                    
                if return_from_ss != True:
                    runtime = 0
                    
                return_from_ss = False
                
                screen.blit(background, (0, 0))
                pygame.display.flip()
        
                break
            
            elif event.type == MOUSEBUTTONUP:
                #if Button1.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button1, 2)
                #    background.blit(font.render(pause_text, True, BLACK), (35,192))
                    
                #if Button2.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button2, 2)
                #    background.blit(font.render("Cancel", True, BLACK), (152,192))
                    
                #if Button3.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button3, 2)
                #    background.blit(font.render("Reboot", True, BLACK), (275,192))
                    
                #if Button4.collidepoint(mouse_pos):
                #    pygame.draw.rect(background, WHITE, Button4, 2)
                #    background.blit(font.render("Power Off", True, BLACK), (386,192))
                
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
                api_version = "0"
                octo_version = "0"
            
            ext_f = "0"
            bed_f = "0"
			
            stateinfo = get_info('connection')
            if stateinfo is not None:
                state = stateinfo['current']['state']
            else:
                state = "Offline"
                progress_completion = 0
                
            if state != "Offline":
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
            background = createSurface(screen, BLACK)
		
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
            if progress_completion is not None and state != 'Offline':
                status_text = "Status: " + state + " (" + `progress_completion` + "%)"
            else:
                status_text = "Status: " + state

            filename_text = ""
            if file_name is not None and state != 'Offline':
                filename_text = "Name:   " + file_name.replace("_", " ").replace(".gcode", "")
            else:
                filename_text = "Name: "

            if file_size is not None and state != 'Offline':
                size_text = "Size:   " + "{:,}".format(file_size) + " Bytes"
            else:
                size_text = "Size:"
            
            ext_c = `ext`
            ext_target_c = `ext_target`
            bed_c = `bed`
            bed_target_c = `bed_target`
            
            if state == 'Offline':
                ext_f = "0"
                bed_f = "0"
            
            bed_space = ""
            if len(bed_f) == 2:
                bed_space = " "
            
            printText(font, WHITE, status_text, background, 5,5)
            printText(font, WHITE, filename_text, background, 5,30)
            printText(font, WHITE, size_text, background, 5,55)
            printText(font, WHITE, "ETA:    %02d:%02d:%02d" % (day, hour, minutes), background, 5, 80)
            printText(font, WHITE, "wlan0:  " + getIPAddr('wlan0').ljust(15), background, 5, 130)
            printText(font, WHITE, "        " + getHWAddr('wlan0').ljust(17), background, 5,155)
            printText(font, WHITE, "eth0:   " + getIPAddr('eth0').ljust(15), background, 5, 180)
            printText(font, WHITE, "        " + getHWAddr('eth0').ljust(17), background, 5, 205)

            #if state != 'Offline':
                #printText(font, WHITE, "Ver: " + api_version + "-" + octo_version, background, 330,5)
                #printText(font, WHITE, "  [ extruder: " + ext_f.rjust(3) + ds + "F / " + ext_c.rjust(3) + ds + "C  " + bed_space + "  bed:    " + bed_space + "    " + bed_f.rjust(3).replace(' ', '') + ds + "F / " + bed_c.rjust(3).replace(' ', '') + ds + "C ]", background, 5, 110)
                #printText(font, WHITE, "  [ target:   " + ext_target_f.rjust(3) + ds + "F / " + ext_target_c.rjust(3) + ds + "C  " + bed_space + "  target:     " + bed_target_f.rjust(3).replace(' ', '') + ds + "F /" + bed_target_c.rjust(3) + ds + "C ]", background, 5, 128)
                #printText(font, WHITE, "%02d:%02d:%02d" % (day, hour, minutes), background, 205, 300)

            #printText(font, WHITE, tzdata.strftime('%m-%d-%Y'), background, 5,300)
            #printText(font, WHITE, tzdata.strftime('%H:%M:%S'), background, 405,300)
            
            #setProgress(background, progress_completion)
    
            # buttons
            #pygame.draw.rect(background, WHITE, Button1, 2)
            #background.blit(font.render(pause_text, True, WHITE), (35,192))
            
            #pygame.draw.rect(background, WHITE, Button2, 2)
            #background.blit(font.render("Cancel", True, WHITE), (152,192))
            
            #pygame.draw.rect(background, WHITE, Button3, 2)
            #background.blit(font.render("Reboot", True, WHITE), (275,192))
            
            #pygame.draw.rect(background, WHITE, Button4, 2)
            #background.blit(font.render("Power Off", True, WHITE), (386,192))
		
            screen.blit(background, (0, 0))
            pygame.display.flip()

            runtime += 1
			
            if runtime == ssaver_time:
                runtime = 0
                screensaver_on = True
        else:
            # fire up the screensaver
            size = [320,480]
			
            background = createSurface(screen, BLACK)
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
                    matrixcode = "MP Mini Select V2 IIIP 3D Printer"
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
                clock.tick(15)
				
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

