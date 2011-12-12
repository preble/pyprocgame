from procgame.game import AttrCollection, GameItem
import unittest

TEST_EVENT='test'

class EventsTest(unittest.TestCase):

	def setUp(self):
		self.attrs = AttrCollection()
		item = GameItem(game=None, name='a', number=1)
		item.tags.append('awesome')
		self.attrs.add(item.name, item)
		item = GameItem(game=None, name='b', number=2)
		self.attrs.add(item.name, item)

	def test_len(self):
		self.assertEqual(len(self.attrs), 2)

	def test_iter(self):
		count = 0
		for item in self.attrs:
			count += 1
		self.assertEqual(count, 2)
	
	def test_tags(self):
		items = self.attrs.items_tagged('awesome')
		self.assertEqual(len(items), 1)
		items = self.attrs.items_tagged('does-not-exist')
		self.assertEqual(len(items), 0)

	def test_attrlookup_str(self):
		item = self.attrs['a']
		self.assertEqual(item.name, 'a')
		self.assertEqual(item.number, 1)

	def test_attrlookup_num(self):
		item = self.attrs[1]
		self.assertEqual(item.name, 'a')
		self.assertEqual(item.number, 1)
	
	def test_remove(self):
		self.attrs.remove(name='a', number=1)
		self.assertEqual(len(self.attrs), 1)
	
	def test_membership(self):
		self.assertTrue(1 in self.attrs)
		self.assertTrue(2 in self.attrs)
		self.assertTrue('a' in self.attrs)
		self.assertTrue('b' in self.attrs)
		self.assertFalse('x' in self.attrs)

	def test_filter(self):
		items = filter(None, self.attrs)
		self.assertEqual(len(items), 2)
		items = filter(lambda item: item.name != None, self.attrs)
		self.assertEqual(len(items), 2)

if __name__ == '__main__':
	unittest.main()
