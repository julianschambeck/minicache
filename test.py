import unittest
import time
from minicache import Minicache

class TestMinicache(unittest.TestCase):
    def setUp(self):
        pass

    def test_get(self):
        self.mini = Minicache(ttl=2)
        self.assertIsNone(self.mini.get(1))
        self.mini.put(1, b'Williams')
        self.assertIsNotNone(self.mini.get(1))
        time.sleep(2.1)
        self.assertIsNone(self.mini.get(1))

    def test_put(self):
        self.mini = Minicache(memory_max=15)
        self.mini.put(1, b'Williams JR')
        self.mini.put(2, b'Jamal')
        # memory max reached, expect to evict first entry
        self.assertEqual(self.mini.memory_usage(), 5)
        self.assertEqual(len(self.mini.values()), 1)

    def test_memory_usage(self):
        self.mini = Minicache()
        self.mini.put(1, b'Williams JR')
        self.mini.put(2, b'Jamal')
        self.assertEqual(self.mini.memory_usage(), 16)
        self.mini.delete(2)
        self.assertEqual(self.mini.memory_usage(), 11)

    def test_ttl_up(self):
        self.mini = Minicache(ttl=2)
        self.mini.put(1, b'Williams JR')
        self.assertFalse(self.mini.is_ttl_up(1))
        time.sleep(2.1)
        self.assertTrue(self.mini.is_ttl_up(1))

if __name__ == '__main__':
    unittest.main()