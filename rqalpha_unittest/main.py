import os
import unittest
from BeautifulReport import BeautifulReport as bf

root_dir = os.path.dirname(__file__)

case_path = root_dir
report_path = os.path.join(root_dir, "report")

suite = unittest.defaultTestLoader.discover(case_path, pattern="Test*.py", top_level_dir=None)
# suite = unittest.TestSuite()
# suite.addTest(unittest.makeSuite(TestModFactorFlow))
bf_run = bf(suite)
bf_run.report(filename='report', report_dir=report_path, description='rqalpha rqalpha_unittest report')
