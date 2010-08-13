import pinproc
import time
import math

machine_type = 'wpc'

def pulse(n, t = 20):
	"""docstring for pulse"""
	pr.driver_pulse(pinproc.decode(str(n)), t)

def main():
	pr = pinproc.PinPROC(machine_type)
	time.sleep(2) # Give P-ROC a second to get going?
	import pygame
	try:
		pygame.init()
		screen = pygame.display.set_mode((128, 32))
		pygame.display.set_caption('P-ROC DMD')
	
		background = pygame.Surface(screen.get_size())
		background = background.convert()
	
		fontSize = 14
		x = 200.0
		while 1:
			background.fill((0, 0, 0))
	
			if pygame.font:
				font = pygame.font.Font(None, fontSize*3)
				text = font.render("This is P-ROC", 1, (150, 150, 150))
				textpos = text.get_rect(center=(x, background.get_height()/2))#(centerx=background.get_width()/2)
				background.blit(text, textpos)
				font = pygame.font.Font(None, fontSize)
				text = font.render("This is P-ROC", 1, (255, 255, 255))
				textpos = text.get_rect(center=(math.cos(time.clock()*5.0)*10.0+background.get_width()/2, math.sin(time.clock()*5.0)*5.0+background.get_height()*0.3))
				background.blit(text, textpos)
				font = pygame.font.Font(None, fontSize*1.5)
				text = font.render("pypinproc", 1, (255, 255, 255))
				textpos = text.get_rect(center=(background.get_width()*0.5, background.get_height()*0.75))
				background.blit(text, textpos)
	
			screen.blit(background, (0,0))
			pygame.display.flip()
	
			surface = pygame.display.get_surface()
			buffer = surface.get_buffer()

			pr.dmd_draw(buffer.raw)
			del buffer
			del surface
			x -= 1
			if x < -200.0:
				x = 200.0
			time.sleep(1/40)
	finally: #except KeyboardInterrupt:
		del pr

#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()