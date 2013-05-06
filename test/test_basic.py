#!/usr/bin/env python
#
#  Test some basic functionality.
#
#===============
#  This is based on a skeleton test file, more information at:
#
#     https://github.com/linsomniac/python-unittest-skeleton

import unittest
import os
import sys
sys.path.append('..')

class test_q_Basic(unittest.TestCase):
	@classmethod
	def setUp(self):
		if os.path.exists('/tmp/q'):
			os.remove('/tmp/q')

	def tearDown(self):
		self.setUp()

	def test_q_Basic(self):
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

unittest.main()
