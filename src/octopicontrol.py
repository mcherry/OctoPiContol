#!/usr/bin/python
# -*- coding: utf-8 -*-

import pygame
import os
import time
import random
import sys
import signal
from datetime import datetime
from pytz import timezone
from pygame.locals import *

# required environment variables for pygame
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/event0')

tzone = "US/Central"

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
		timedata = datetime.now(timezone(timezones[index]))
		timestring = timedata.strftime('%X %Z %z') + locations[index] + timezones[index]
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

def signal_handler(signal, frame):
  print 'Caught signal: {}'.format(signal)
  time.sleep(1)
  pygame.quit()
  sys.exit(0)

def main():
    runtime = 0
    ssaver_time = 180
    screensaver_on = False
    return_from_ss = False
	

    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((480, 320))
    pygame.mouse.set_visible(False)

    # setup signals to catch ctrl-c
    #signal.signal(signal.SIGTERM, signal_handler)
    #signal.signal(signal.SIGINT, signal_handler)
    
    # main loop
    pos = (0, 0)
    while 1:
        for event in pygame.event.get():
            if event.type is MOUSEBUTTONUP:
                # disable mousebuttonup events while procesing the event.
		# this is an attempt to not process mousebuttonup events
		# so fast that the time "skips" an index
		pygame.event.set_blocked(MOUSEBUTTONUP)
		time.sleep(0.25)

		#pos = pygame.mouse.get_pos()
		#print pos
				
		if return_from_ss != True:
                    runtime = 0
                    return_from_ss = False
                    break
				
		elif event.type == QUIT:
                    return

		if screensaver_on is False:
                    # Fill background
                    background = pygame.Surface(screen.get_size())
                    background = background.convert()
                    background.fill((0, 0, 0))

                    # create fonts
                    font = pygame.font.Font(None, 46)

                    # format the date and time strings
                    #local_time = tzdata.strftime('%X %Z')
                    #local_date = tzdata.strftime('%x')

                    # render each string with a font in a certain color
                    statustext = font.render("Status:", 1, (250, 250, 250))
                    #datetext = font.render(local_date, 1, (250, 250, 250))
                    #tzinfo = font.render(locations[index], 1, (250, 250, 250))
			
                    # figure out where to place time
                    #timepos = timetext.get_rect()
                    #timepos.centerx = background.get_rect().centerx
                    #timepos.centery = background.get_rect().centery - 40

                    # figure out where to place date
                    #datepos = datetext.get_rect()
                    #datepos.centerx = background.get_rect().centerx
                    #datepos.centery = background.get_rect().centery + 40
		
                    # put the readable name at 10, 10
                    background.blit(statustext, (10, 10))
                    #background.blit(timetext, timepos)
                    #background.blit(datetext, datepos)
			
                    # Blit everything to the screen
                    screen.blit(background, (0, 0))
                    pygame.display.flip()

                    # wait a second to refresh
                    runtime += 1
			
                    if runtime == ssaver_time:
                        runtime = 0
			screensaver_on = True
			
                    # re-enable mousebutton up events after processing time
                    pygame.event.set_allowed(MOUSEBUTTONUP)
                    time.sleep(1)
		
		else:
                    # fire up the screensaver
                    size = [480,320]
			
                    background = pygame.Surface(screen.get_size())
                    background = background.convert()
                    background.fill((0, 0, 0))
                    screen.blit(background, (0, 0))
                    pygame.display.flip()
					
                    delay = DelaySwitch(25)

                    text_width=15
                    text = pygame.font.SysFont(None, text_width)

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
                            groups.append(Group([pos, -text.get_height()], speed))
					
                            if random.randint(0,50) == 50:
                                # "matrix code" is a string made up of the current timezone/time/date
                                timedata = datetime.now(timezone(timezones[index]))
                                timestring = timedata.strftime('%X %Z %z') + locations[index] + timezones[index]
                                code = list(timestring)
                                random.shuffle(code, random.random)
                                pos = [random.randint(1,size[0]/text_width+1)*text_width-text_width/2, random.randint(1,size[1]/text.get_height()+1)*text.get_height()]
                                groups.append(CodePartical(pos, random.randint(0,len(code)-1), code))

				for group in groups:
                                    group.modernize(text, size)
                                    if group.dead:
					groups.remove(group)
						
				rects = []
				for group in groups:
                                    for rect in group.render(screen, text):
                                        rects.append(rect)
						
				delay.update()
				pygame.display.flip()
				
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