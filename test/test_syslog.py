#!/usr/bin/env python
#
#  Test the output to syslog.
#
#===============
#  This is based on a skeleton test file, more information at:
#
#     https://github.com/linsomniac/python-unittest-skeleton

import unittest
import os
import sys
sys.path.append('..')

class test_q_Syslog(unittest.TestCase):
	@classmethod
	def setUp(self):
		if os.path.exists('/tmp/q'):
			os.remove('/tmp/q')

	def tearDown(self):
		self.setUp()

	def test_q_Disable(self):
		import q
		q.use_syslog()

		q.q('Test message')
		self.assertFalse(os.path.exists('/tmp/q'))

unittest.main()
