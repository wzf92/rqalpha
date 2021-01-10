#!/usr/bin/env python
# -*- coding: utf-8 -*-
from rqalpha import run
import unittest
from BeautifulReport import BeautifulReport as bf
import os
import hashlib
import yaml
import glob
import sh


class TestModFactorFlow(unittest.TestCase):
    def setUp(self):
        self._root_path = os.path.dirname(__file__)
        del_path = os.path.join(self._root_path, "test_output", "*")
        for f in glob.glob(del_path):
            os.remove(f)

    def tearDown(self):
        pass

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
        config = self.load_config(self._p('conf/1_test.yml'))
        try:
            run(config)
        except SystemExit as e:
            pass
        diff_res = sh.diff(self._p("test_output/I88_flow.csv"), self._p("expect_output/1_I88_flow.csv"))
        self.assertEqual(diff_res, "")


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestModFactorFlow))
    bf_run = bf(suite)
    bf_run.report(filename='report',report_dir='/tmp/unittest_report', description='rqalpha rqalpha_unittest report')
