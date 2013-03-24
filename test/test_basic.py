#!/usr/bin/env python
# vim: set ts=4 sw=4 et sts=4 ai:
#
# Test some basic functionality.
#

import unittest
import os
import sys
sys.path.append('..')

class TestQBasic(unittest.TestCase):

    def setUp(self):
        if os.path.exists('/tmp/q'):
            os.remove('/tmp/q')

    def tearDown(self):
        self.setUp()

    def test_q_basic(self):
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
