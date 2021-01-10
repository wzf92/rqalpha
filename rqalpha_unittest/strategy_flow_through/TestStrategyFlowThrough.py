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


class TestStrategyFlowThrough(unittest.TestCase):
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
        abs_flow_dir = os.path.join(self._root_path, config["mod"]["sys_analyser"]["report_save_path"])
        config["base"]["strategy_file"] = abs_strategy_path
        config["mod"]["sys_analyser"]["report_save_path"] = abs_flow_dir
        return config

    def _p(self, path):
        return os.path.join(self._root_path, path)


    def fetch_fields(self, input_path, output_path):
        sh.awk(sh.cat(input_path), "-F,", '{print $1, $3, $5, $6}', _out=output_path)


    def test01(self):
        config = self.load_config(self._p('conf/1_test.yml'))
        try:
            run(config)
        except SystemExit as e:
            pass
        self.fetch_fields(self._p("test_output/trades.csv"), self._p("test_output/trades_filter.csv"))
        diff_res = sh.diff(self._p("test_output/trades_filter.csv"), self._p("expect_output/1_trades_filter.csv"))
        self.assertEqual(diff_res, "")


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStrategyFlowThrough))
    bf_run = bf(suite)
    bf_run.report(filename='report',report_dir='/tmp/unittest_report', description='rqalpha rqalpha_unittest report')
