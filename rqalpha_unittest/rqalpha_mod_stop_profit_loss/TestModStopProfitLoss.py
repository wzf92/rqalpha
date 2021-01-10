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


class TestModStopProfitLoss(unittest.TestCase):
    def setUp(self):
        self._root_path = os.path.dirname(__file__)
        del_path = os.path.join(self._root_path, "test_output", "*")
        for f in glob.glob(del_path):
            os.remove(f)

    def load_config(self, config_path):
        with open(config_path, 'r') as config_file:
            config = yaml.load(config_file.read())
        abs_strategy_path = os.path.join(self._root_path, config["base"]["strategy_file"])
        abs_flow_dir = os.path.join(self._root_path, config["mod"]["stop_profit_loss"]["log_dir"])
        config["base"]["strategy_file"] = abs_strategy_path
        config["mod"]["stop_profit_loss"]["log_dir"] = abs_flow_dir
        return config

    def _p(self, path):
        return os.path.join(self._root_path, path)


    def test01(self):
        config = self.load_config(self._p('conf/1_test.yml'))
        try:
            run(config)
        except SystemExit as e:
            pass
        diff_res = sh.diff(self._p("test_output/I88_stop_profit_loss.csv"), self._p("expect_output/1_I88_stop_profit_loss.csv"))
        self.assertEqual(diff_res, "")
        # with open(self._p("test_output/I88_stop_profit_loss.csv"), "rb") as f:
        #     data = f.read()
        #     file_md5 = hashlib.md5(data).hexdigest()
        # with open(self._p("expect_output/1_I88_stop_profit_loss.csv"), "rb") as f:
        #     data = f.read()
        #     exp_file_md5 = hashlib.md5(data).hexdigest()
        # self.assertEqual(exp_file_md5, file_md5)


    def test02(self):
        config = self.load_config(self._p('conf/2_test.yml'))
        try:
            run(config)
        except SystemExit as e:
            pass
        diff_res = sh.diff(self._p("test_output/I88_stop_profit_loss.csv"), self._p("expect_output/2_I88_stop_profit_loss.csv"))
        self.assertEqual(diff_res, "")

        # with open(self._p("test_output/I88_stop_profit_loss.csv"), "rb") as f:
        #     data = f.read()
        #     file_md5 = hashlib.md5(data).hexdigest()
        # with open(self._p("expect_output/2_I88_stop_profit_loss.csv"), "rb") as f:
        #     data = f.read()
        #     exp_file_md5 = hashlib.md5(data).hexdigest()
        # self.assertEqual(exp_file_md5, file_md5)

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestModStopProfitLoss))
    bf_run = bf(suite)
    bf_run.report(filename='report',report_dir='/tmp/unittest_report', description='rqalpha rqalpha_unittest report')
