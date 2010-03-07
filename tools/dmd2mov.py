import sys, os

try:
	import objc
	from Foundation import *
	from QTKit import *
except ImportError:
	print "Error importing Mac OS X PyObjC frameworks.  This application requires Mac OS X."
	sys.exit(1)

sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
from procgame import *

def NSOvalFill(rect):
	thePath = NSBezierPath.bezierPath()
	thePath.appendBezierPathWithOvalInRect_(rect)
	thePath.fill()

colors = []
for c in range(16):
	q = (float(c)/15.0)
	colors.append(NSColor.colorWithDeviceRed_green_blue_alpha_(1.0, 0.5, 0.0, q))

def dmd_frame_as_nsimage(frame):
	global colors
	dot_size=8
	image = NSImage.alloc().initWithSize_(NSMakeSize(frame.width*dot_size, frame.height*dot_size))
	image.lockFocus()
	NSColor.blackColor().set()
	NSRectFill(NSMakeRect(0, 0, frame.width*dot_size, frame.height*dot_size))
	for y in range(frame.height):
		for x in range(frame.width):
			color = frame.get_dot(x, y)
			if color == 0: continue
			if not color in range(len(colors)):
				print "Skipping bad color", color, "at", x, y
			else:
				colors[color].set()
			NSRectFill(NSMakeRect(x * dot_size + 1, (frame.height - 1 - y) * dot_size + 1, dot_size - 2, dot_size - 2))
	image.unlockFocus()
	return image

def dmd2mov(input_path, output_path, fps):
	movie = QTMovie.alloc().initToWritableData_error_(NSMutableData.data(), None)[0]
	anim = dmd.Animation().load(input_path)
	attrs = {QTAddImageCodecType:"mp4v"}
	for frame in anim.frames:
		image = dmd_frame_as_nsimage(frame)
		movie.addImage_forDuration_withAttributes_(image, QTMakeTimeWithTimeInterval(1.0/float(fps)), attrs)
		movie.setCurrentTime_(movie.duration())
		print movie.duration(),"\r",
		sys.stdout.flush()
	print
	movie.writeToFile_withAttributes_(output_path, {QTMovieFlatten: True})

def main():
	if len(sys.argv) < 4:
		print("Usage: %s <input.dmd> <output.mov> <frames/second>"%(sys.argv[0]))
		return
	dmd2mov(sys.argv[1], sys.argv[2], fps=int(sys.argv[3]))

if __name__ == "__main__":
	main()
