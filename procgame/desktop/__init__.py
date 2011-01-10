# We have two implementations of the Desktop class.  One for pyglet, one for pygame.
# The pyglet version is prettier, so we will try to import it first.
try:
	import pyglet as _pyglet
except ImportError:
	_pyglet = None

if _pyglet:
	from desktop_pyglet import Desktop
else:
	from desktop_pygame import Desktop
