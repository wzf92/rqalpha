#!/usr/bin/env python
# -*- coding: utf-8 -*-
from rqalpha import run
import unittest
from BeautifulReport import BeautifulReport as bf
import os
import hashlib
import yaml

class TestModCalcFlowFactor(unittest.TestCase):
    def setUp(self):
        self._root_path = os.path.dirname(__file__)

    def load_config(self, config_path):
        with open(config_path, 'r') as config_file:
            config = yaml.load(config_file.read())
        abs_strategy_path = os.path.join(self._root_path, config["base"]["strategy_file"])
        abs_flow_dir = os.path.join(self._root_path, config["mod"]["factor_flow"]["log_dir"])
        config["base"]["strategy_file"] = abs_strategy_path
        config["mod"]["factor_flow"]["log_dir"] = abs_flow_dir
        return config

    def _p(self, path):
        return os.path.join(self._root_path, path)


    def test01(self):
        config = self.load_config(self._p('conf/test01.yml'))
        try:
            run(config)
        except SystemExit as e:
            pass
        with open(self._p("test_output/I88_flow.csv"), "rb") as f:
            data = f.read()
        file_md5 = hashlib.md5(data).hexdigest()
        self.assertEqual(file_md5, "701676a67efc5c2e85d89509715c44de")


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestModCalcFlowFactor))
    bf_run = bf(suite)
    bf_run.report(filename='report',report_dir='/tmp/unittest_report', description='rqalpha rqalpha_unittest report')
    unittest.main()
