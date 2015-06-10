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

    def assertInQLog(self, string):
        self.assertTrue(os.path.exists('/tmp/q'))
        self.assertIn(string, open('/tmp/q', 'r').read())

    def test_q_log_message(self):
        import q
        q.q('Test message')
        self.assertInQLog('Test message')

    def test_q_function_call(self):
        import q

        @q.t
        def test(arg):
            return 'RetVal'

        self.assertEqual('RetVal', test('ArgVal'))

        self.assertInQLog('ArgVal')
        self.assertInQLog('RetVal')


unittest.main()
