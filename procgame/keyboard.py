import sys
import procgame
import pinproc
from threading import Thread
import random
import string
import time
import locale
import math
import copy
import pygame
from pygame.locals import *
import dmd

pygame.init()
screen_multiplier = 2
screen = pygame.display.set_mode((128*screen_multiplier, 32*screen_multiplier))
pygame.display.set_caption('Press CTRL-C to exit')
rect = pygame.Surface([128*screen_multiplier,32*screen_multiplier])
#circle = pygame.Surface([300, 50])
#line = pygame.Surface([300,50])
#color = pygame.Color(100,0,0,100)
#rect = pygame.Surface([128,32])
#pygame.draw.line(line, color, [0,25], [128,25], 2)
#pygame.draw.circle(circle, color, [125,25], 20,8)
#screen.blit(line, [0,0])
#pygame.display.flip()
#screen.blit(circle, [0,0])
#pygame.display.flip()

class KeyboardHandler():
	"""docstring for KeyboardHandler"""
	def __init__(self):
		self.ctrl = 0
		self.old_frame = dmd.Frame(128,32)
		self.old_frame.fill_rect(0,0,128,32,0)
		self.i = 0

	def get_keyboard_events(self):
		key_events = []
		for event in pygame.event.get():
			key_event = {}
			if event.type == KEYDOWN:
				if event.key == K_RCTRL or event.key == K_LCTRL:
					self.ctrl = 1
				if event.key == K_c:
					if self.ctrl == 1:
						key_event['type'] = 99
						key_event['value'] = 'quit'
				elif (event.key == K_ESCAPE):
					key_event['type'] = 99
					key_event['value'] = 'quit'
				elif (event.key == K_RSHIFT):
					key_event['type'] = 1
					key_event['value'] = 1
				elif (event.key == K_LSHIFT):
					key_event['type'] = 1
					key_event['value'] = 3
			elif event.type == KEYUP:
				if event.key == K_RCTRL or event.key == K_LCTRL:
					self.ctrl = 0
				elif (event.key == K_RSHIFT):
					key_event['type'] = 2
					key_event['value'] = 1
				elif (event.key == K_LSHIFT):
					key_event['type'] = 2
					key_event['value'] = 3
			if len(key_event):
				key_events.append(key_event)
		return key_events

	def draw(self, frame):

		# Use adjustment to add a one pixel border around each dot, if
		# the screen size is large enough to accomodate it.
		if screen_multiplier >= 4:
			adjustment = -1
		else:
			adjustment = 0

		# Keep a list of the rectangles (dots) being changed (a dirty list).
		# This should increase screen update times.
		changed_rect_list = []

		for y in range(frame.height):
			for x in range(frame.width):

				dot = frame.get_dot(x, y)
				#if True:
				if dot != self.old_frame.get_dot(x,y):
					color_val = dot*16
					color = pygame.Color(color_val, color_val, color_val)
					
					dot = pygame.Rect(x*screen_multiplier, \
       	                                           y*screen_multiplier, \
       	                                           screen_multiplier+adjustment, \
       	                                           screen_multiplier+adjustment)
					
					pygame.draw.rect(rect, color, dot, 0)
					changed_rect_list += [dot]
					#pygame.draw.circle(rect, color, [x*screen_multiplier,y*screen_multiplier], screen_multiplier/2, 0)
					
		screen.blit(rect, [0,0])	
		pygame.display.update(changed_rect_list)

		self.old_frame = frame.copy()
