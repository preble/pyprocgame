
class Event(object):
	"""An Event dispatched by :class:`EventManager`."""
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

class EventManager(object):
	"""EventManager dispatches events to event handlers."""
	
	def __init__(self):
		super(EventManager, self).__init__()
		# __handlers is keyed off of the event name, with the contents being a hash of the object to the handler arrays:
		# __handlers[name][object][handler_index]
		self.__handlers = {}
	
	def add_event_handler(self, name, handler, object=None):
		"""Handlers take a single parameter, the Event object being dispatched."""
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
	
	def dispatch_event(self, event):
		"""Dispatch the given event."""
		if event.name in self.__handlers:
			obj_keyed = self.__handlers[event.name]
			if None in obj_keyed:
				for handler in obj_keyed[None]:
					handler(event)
			if event.object in obj_keyed:
				for handler in obj_keyed[event.object]:
					handler(event)
	
	def dispatch(self, name, object=None, info=None):
		"""Dispatch an event with the given properties."""
		event = Event(name, object, info)
		self.dispatch_event(event)


