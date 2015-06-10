#!/usr/bin/env python
# vim: set ts=4 sw=4 et sts=4 ai:
#
# Test some basic functionality.
#

import unittest
import os
import sys

qpath = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..'))
sys.path.insert(0, qpath)


class TestQBasic(unittest.TestCase):

    def setUp(self):
        if os.path.exists('/tmp/q'):
            os.remove('/tmp/q')

    def tearDown(self):
        self.setUp()

    def assertInQLog(self, string):
        # Check the log file exists.
        self.assertTrue(os.path.exists('/tmp/q'))

        # Read in the data
        f = open('/tmp/q', 'r')
        logdata = f.read()
        f.close()

        # Check the string is found in the log file
        try:
            self.assertIn(string, logdata)
        except AttributeError:
            self.assertTrue(string in logdata)

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
