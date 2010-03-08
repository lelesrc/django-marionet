# -*- coding: utf-8 -*-
import unittest
import os, sys

from portlet_test import *

suite = unittest.TestSuite()
for test in [
    PortletTest
    ]:
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(test))

if '__main__' == __name__:
    unittest.TextTestRunner(verbosity=2).run(suite)

