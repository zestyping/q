#!/usr/bin/env python
#
#  Test the disabling of trace and show functions.
#
#===============
#  This is based on a skeleton test file, more information at:
#
#     https://github.com/linsomniac/python-unittest-skeleton

import unittest
import os
import sys
sys.path.append('..')

class test_q_Disable(unittest.TestCase):
	@classmethod
	def setUp(self):
		if os.path.exists('/tmp/q'):
			os.remove('/tmp/q')

	def tearDown(self):
		self.setUp()

	def test_q_Disable(self):
		import q

		@q.t
		def test(arg):
			return 'RetVal'

		q.q('Test message')
		self.assertEqual('RetVal', test('foo'))
		self.assertTrue(os.path.exists('/tmp/q'))
		self.assertIn('Test message', open('/tmp/q', 'r').read())
		self.assertIn('foo', open('/tmp/q', 'r').read())
		self.assertIn('RetVal', open('/tmp/q', 'r').read())

		q.disable()
		@q.t
		def test(arg):
			return 'RetVal2'

		q.q('Another message')
		self.assertEqual('RetVal2', test('bar'))
		self.assertNotIn('Another message', open('/tmp/q', 'r').read())
		self.assertNotIn('bar', open('/tmp/q', 'r').read())
		self.assertNotIn('RetVal2', open('/tmp/q', 'r').read())

unittest.main()
