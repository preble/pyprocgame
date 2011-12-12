from procgame.events import EventManager
import unittest

TEST_EVENT='test'

class EventsTest(unittest.TestCase):

	def setUp(self):
		self.events = EventManager()
		self.events.add_event_handler(name=TEST_EVENT, object=None, handler=self.handler_no_obj)
		self.events.add_event_handler(name=TEST_EVENT, object=self, handler=self.handler_obj)
		self.flag = 0

	def handler_no_obj(self, event):
		self.flag += 1
	def handler_obj(self, event):
		self.flag += 2
	
	def test_setup(self):
		self.assertEqual(self.flag, 0)

	def test_unknown_name(self):
		self.events.post(name=TEST_EVENT+'blah', object=None)
		self.assertEqual(self.flag, 0)

	def test_None_obj(self):
		self.events.post(name=TEST_EVENT, object=None)
		self.assertEqual(self.flag, 2)

	def test_obj_set(self):
		self.events.post(name=TEST_EVENT, object=self)
		self.assertEqual(self.flag, 3)

	def test_obj_other(self):
		self.events.post(name=TEST_EVENT, object='1234')
		self.assertEqual(self.flag, 1)

	def test_remove(self):
		self.events.remove_event_handler(handler=self.handler_obj)
		self.events.post(name=TEST_EVENT, object=self)
		self.assertEqual(self.flag, 1)
	

if __name__ == '__main__':
	unittest.main()
