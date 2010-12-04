import os
import sys

def find_file_in_path(name, paths):
	"""Search *paths* for a file named *name*.  Return the path, or ``None`` if not found."""
	for path in paths:
		path = os.path.join(os.path.expanduser(path), name)
		if os.path.isfile(path):
			return path
	return None

def get_class( kls, path_adj='/.' ):
	"""Returns a class for the given fully qualified class name, *kls*.

	Source: http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname"""
	sys.path.append(sys.path[0]+path_adj)
	parts = kls.split('.')
	module = ".".join(parts[:-1])
	m = __import__( module )
	for comp in parts[1:]:
		m = getattr(m, comp)
	return m

class const:
	"""From http://code.activestate.com/recipes/65207/"""
	def __setattr__(self, attr, value):
		if hasattr(self, attr):
			raise ValueError, 'const %s already has a value and cannot be written to' % attr
		self.__dict__[attr] = value

class BlackHole(object):
	def __init__(self, *args):
		pass
	def noop(self, *args, **kwargs):
		pass
	def __getattr__(self, name):
		return self.noop
