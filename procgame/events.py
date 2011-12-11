
class Event(object):
	"""Describes an event dispatched by :class:`EventManager`."""
	
	name = None
	"""Name of the event."""
	object = None
	"""Object this event is associated with."""
	info = None
	"""Any information associated with the event."""
	
	def __init__(self, name, object, info):
		super(Event, self).__init__()
		self.name = name
		self.object = object
		self.info = info

global_event_manager = None

class EventManager(object):
	"""Dispatches events to event handlers.  Until better documentation is created, it may be helpful to know that this class is strongly influenced by the Cocoa class :class:`NSNotificationCenter`.
	
	Most users will want to obtain the default instance using :meth:`default`::
	
		EventManager.default().add_event_handler(...)
	"""
	
	@classmethod
	def default(cls):
		"""Returns the default (shared) EventManager instance."""
		global global_event_manager
		if not global_event_manager:
			global_event_manager = cls()
		return global_event_manager
	
	def __init__(self):
		super(EventManager, self).__init__()
		# __handlers is keyed off of the event name, with the contents being a hash of the object to the handler arrays:
		# __handlers[name][object][handler_index]
		self.__handlers = {}
	
	def add_event_handler(self, name, handler, object=None):
		"""Handlers take a single parameter, the :class:`Event` object being posted."""
		if name not in self.__handlers:
			self.__handlers[name] = {object:[handler]}
		else:
			obj_keyed = self.__handlers[name]
			if object not in obj_keyed:
				obj_keyed[object] = [handler]
			elif handler not in obj_keyed[object]:
				obj_keyed[object].append(handler)
	
	def remove_event_handler(self, handler):
		"""Remove the given handler."""
		# Search __handlers to remove it.
		for name in self.__handlers:
			obj_keyed = self.__handlers[name]
			for object in obj_keyed:
				handlers = obj_keyed[object]
				if handler in handlers:
					handlers.remove(handler)
	
	def post_event(self, event):
		"""Post the given :class:`Event` instance. Blocks while the resulting handlers are called."""
		if event.name in self.__handlers:
			obj_keyed = self.__handlers[event.name]
			if None in obj_keyed:
				for handler in obj_keyed[None]:
					handler(event)
			if event.object in obj_keyed:
				for handler in obj_keyed[event.object]:
					handler(event)
	
	def post(self, name, object=None, info=None):
		"""Post an :class:`Event` with the given properties."""
		event = Event(name, object, info)
		self.post_event(event)


