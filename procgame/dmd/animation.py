import os
import struct
import yaml
import sqlite3
import bz2
import StringIO
import time
import Image
from procgame.dmd import Frame
from procgame import config
import logging
import re

try:
	import Image
except ImportError:
	Image = None

# Global reference; use AnimationCacheManager.shared_manager() to create and reference.
shared_cache_manager = None

warned_cache_disabled = False

class AnimationCacheManager(object):
	def __init__(self, path):
		self.path = os.path.expanduser(path)
		if not os.path.exists(self.path):
			os.makedirs(self.path)
		self.load()
		# TODO: Check cache for deleted files?
	
	def __del__(self):
		self.conn.close()
		del self.conn
	
	def shared_manager():
		"""Returns a reference to the global, shared manager, if configured by the
		``dmd_cache_path`` in :mod:`procgame.config`."""
		global shared_cache_manager
		if not shared_cache_manager:
			path = config.value_for_key_path('dmd_cache_path')
			if path:
				shared_cache_manager = AnimationCacheManager(path)
			else:
				shared_cache_manager = None
		return shared_cache_manager
	shared_manager = staticmethod(shared_manager)
	
	def database_path(self):
		return os.path.join(self.path, 'cache.db')
	
	def load(self):
		DATABASE_VERSION = 1
		CREATE_VERSION_TABLE = '''create table if not exists version (version integer)'''
		CREATE_ENTRIES_TABLE = '''create table if not exists entries (path text, created integer, accessed integer, compression text, data blob)'''
		self.conn = sqlite3.connect(self.database_path())
		self.conn.execute(CREATE_VERSION_TABLE)
		
		# Now check for any existing version information:
		c = self.conn.cursor()
		c.execute('''select version from version limit 1''')
		result = c.fetchone()
		if not result:
			c.execute('''insert into version values (?)''', (DATABASE_VERSION,))
		else:
			(version,) = result
			if version == DATABASE_VERSION:
				pass # we are up to date
			else:
				import pdb; pdb.set_trace()
				logging.getLogger('game.dmdcache').warning('DMD cache database version (%d) is not current (%d).  Cache will be rebuilt.', version, DATABASE_VERSION)
				del self.conn
				os.remove(self.database_path())
				return self.load()
		
		self.conn.execute(CREATE_ENTRIES_TABLE)
		self.conn.commit()
	
	def invalidate_path(self, path):
		self.conn.execute('''delete from entries where path=?''', (path,))
	
	def get_at_path(self, path, compare_created_time = None):
		"""Attempt to retrieve data from the cache for *path*; returns ``None`` if not present.
		If the created time on the cache entry is before *compare_created_time*, ``None`` will be returned."""
		self.conn.execute('''update entries set accessed=?''', (int(time.time()),))
		c = self.conn.cursor()
		c.execute('''select data, created from entries where path=?''', (path,))
		result = c.fetchone()
		if not result:
			return None
		(data, created) = result
		if compare_created_time and compare_created_time > created:
			return None
		else:
			return bz2.decompress(data)
	
	def set_at_path(self, path, data):
		"""Save *data* for the given *path* in the cache."""
		self.invalidate_path(path)
		data = bz2.compress(data)
		created = accessed = int(time.time())
		self.conn.execute('''insert into entries values (?, ?, ?, ?, ?)''', (path, created, accessed, 'bzip2', sqlite3.Binary(data)))
		self.conn.commit()


class Animation(object):
	"""An ordered collection of :class:`~procgame.dmd.Frame` objects."""
	
	width = None
	"""Width of each of the animation frames in dots."""
	height = None
	"""Height of each of the animation frames in dots."""
	frames = []
	"""Ordered collection of :class:`~procgame.dmd.Frame` objects."""
	
	def __init__(self):
		"""Initializes the animation."""
		super(Animation, self).__init__()
		self.frames = []

	def load(self, filename, allow_cache=True):
		"""Loads *filename* from disk.  The native animation format is the
		:ref:`dmd-format`, which can be created using :ref:`tool-dmdconvert`, or
		`DMDAnimator <https://github.com/preble/DMDAnimator>`_.
		
		This method also supports loading common image formats such as PNG, GIF,
		and so forth using
		`Python Imaging Library <http://www.pythonware.com/products/pil/>`_.
		Note that loading such images can be time-consuming.  As such, a caching
		facility is provided.  To enable animation caching, provide a path using the
		``dmd_cache_path`` key in :ref:`config-yaml`.  Note that only non-native
		images are cached (.dmd files are not cached).
		
		*filename* can be a string or a list.  If it is a list, the images pointed
		to will be appended to the animation.
		"""
		
		# Allow the parameter to be a single filename, or a list of filenames.
		paths = list()
		if type(filename) != list:
			if re.search("%[0-9]*d", filename):
				frame_index = 0
				while True:
					tmp_filename = filename % (frame_index)
					if os.path.exists(tmp_filename):
						paths += [tmp_filename]
						frame_index += 1
					else:
						break;
			else:
				paths += [filename]
				
		paths = map(os.path.abspath, paths)
		
		# The path that is used as the key in the database
		key_path = paths[0]
		
		self.frames = []
		
		animation_cache = None
		if allow_cache:
			animation_cache = AnimationCacheManager.shared_manager()
		
		logger = logging.getLogger('game.dmdcache')
		t0 = time.time()
		data = None
		
		if animation_cache:
			# Check the cache for this data:
			if os.path.exists(key_path):
				data = animation_cache.get_at_path(key_path, os.path.getmtime(key_path))
	
		# If there was data in the cache:
		if data:
			# If it was in the cache, we know that it is in the dmd format:
			self.populate_from_dmd_file(StringIO.StringIO(data))
			# print "Loaded", path, "from cache",
			logger.debug('Loaded "%s" from cache in %0.3fs', key_path, time.time()-t0)
		else:
			# Not in the cache, so we must load from disk:
				
			# Iterate over the provided paths:
			for path in paths:
			
				with open(path, 'rb') as f:
					# Opening from disk.  It may be a DMD, or it may be another format.
					# We keep track of the DMD data representation so we can save it to
					# the cache.
					if path.endswith('.dmd'):
						# Note: Right now we don't cache .dmd files.
						self.populate_from_dmd_file(f)
					else:
						logger.info('Loading %s...', path) # Log for images...
						global warned_cache_disabled
						if not animation_cache and not warned_cache_disabled and allow_cache:
							logger.warning('Loading image file with caching disabled; set dmd_cache_path in config to enable.')
							warned_cache_disabled = True
						
						# It is some other file format.  We will use PIL to open it
						# and then process it into a .dmd format.
						self.populate_from_image_file(path, f)
					
			# Now use our normal save routine to get the DMD format data:
			stringio = StringIO.StringIO()
			self.save_to_dmd_file(stringio)
			dmd_data = stringio.getvalue()
		
			# Finally store the data in the cache:	
			if animation_cache:
				print "Storing in the cache: ", key_path
				animation_cache.set_at_path(key_path, dmd_data)
					
			logger.debug('Loaded "%s" from disk in %0.3fs', key_path, time.time()-t0)
			
		return self

	def save(self, filename):
		"""Saves the animation as a .dmd file at the given location, `filename`."""
		if self.width == None or self.height == None:
			raise ValueError, "width and height must be set on Animation before it can be saved."
		with open(filename, 'wb') as f:
			self.save_to_dmd_file(f)


	def populate_from_image_file(self, path, f):
		
		if not Image:
			raise RuntimeError, 'Cannot open non-native image types without Python Imaging Library: %s' % (path)
		
		src = Image.open(f)

		(w, h) = src.size
		if len(self.frames) > 0 and (w != self.width or h != self.height):
			raise ValueError, "Image sizes must be uniform!  Anim is %dx%d, image is %dx%d" % (w, h, self.width, self.height)

		(self.width, self.height) = (w, h)

		if path.endswith('.gif'):
			from . import animgif
			self.frames += animgif.gif_frames(src)
		else:
			alpha = None
			try:
				alpha = Image.fromstring('L', src.size, src.tostring('raw', 'A'))
			except:
				pass # No alpha channel available?

			reduced = src.convert("L")

			frame = Frame(w, h)

			# Construct a lookup table from 0-255 to 0-15:
			eight_to_four_map = [0] * 256
			for l in range(256):
				eight_to_four_map[l] = int(round((l/255.0) * 15.0))
			
			for x in range(w):
				for y in range(h):
					color = eight_to_four_map[reduced.getpixel((x,y))]
					if alpha:
						color += eight_to_four_map[alpha.getpixel((x,y))] << 4
					frame.set_dot(x=x, y=y, value=color)

			self.frames.append(frame)
		

	def populate_from_dmd_file(self, f):
		f.seek(0, os.SEEK_END) # Go to the end of the file to get its length
		file_length = f.tell()
		f.seek(4) # Skip over the 4 byte DMD header.
		frame_count = struct.unpack("I", f.read(4))[0]
		self.width = struct.unpack("I", f.read(4))[0]
		self.height = struct.unpack("I", f.read(4))[0]
		if file_length != 16 + self.width * self.height * frame_count:
			raise ValueError, "File size inconsistent with header information.  Old or incompatible file format?"
		for frame_index in range(frame_count):
			str_frame = f.read(self.width * self.height)
			new_frame = Frame(self.width, self.height)
			new_frame.set_data(str_frame)
			self.frames.append(new_frame)

	def save_to_dmd_file(self, f):
		header = struct.pack("IIII", 0x00646D64, len(self.frames), self.width, self.height)
		if len(header) != 16:
			raise ValueError, "Packed size not 16 bytes as expected: %d" % (len(header))
		f.write(header)
		for frame in self.frames:
			f.write(frame.get_data())


