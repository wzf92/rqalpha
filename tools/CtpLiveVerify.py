import Kline2HDF5
import HDF5Reader
import sys
import os
import datetime
import json
from rqalpha import run_file
from SendMail import QqMail
import unittest

def parse_json(cfg_name):
    try:
        f = open(cfg_name, 'r')
    except IOError:
        print("Error: open configuration file \"%s\" failed" % cfg_name)
        exit(1)
    return json.loads(f.read())

def ctplive_filter(line):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    #today = "2020-12-16"
    return today in line


def backtrace_filter(line):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    #today = "2020-12-16"
    return today in line


class TestCtpLiveTrades(unittest.TestCase):
    def __init__(self, ctp_trade_log_path, backtrace_trade_log_path, backtrace_flow_log_path, ctp_trade_log_filter = None, backtrace_trade_log_filter = None, backtrace_flow_log_filter = None):
        self._ctp_trade_log_path = ctp_trade_log_path
        self._backtrace_trade_log_path = backtrace_trade_log_path
        self._backtrace_flow_log_path = backtrace_flow_log_path
        self._ctp_trade_log_filter = ctp_trade_log_filter
        self._backtrace_trade_log_filter = backtrace_trade_log_filter
        self._backtrace_flow_log_filter = backtrace_flow_log_filter

    def get_filter_lines(self, path, filter):
        filter_lines = []
        with open(path, 'r') as raw_log:
            lines = raw_log.readlines()
            for l in lines:
                if filter and not filter(l):
                    continue
                l = l.strip('\n')
                filter_lines.append(l)
        return filter_lines


    def test_trades_same(self):
        self.assertTrue(os.path.exists(self._ctp_trade_log_path))
        self.assertTrue(os.path.exists(self._backtrace_trade_log_path))
        self.assertTrue(os.path.exists(self._backtrace_flow_log_path))
        ctp_trade_log_filter_lines = self.get_filter_lines(self._ctp_trade_log_path, self._ctp_trade_log_filter)
        backtrace_trade_log_filter_lines = self.get_filter_lines(self._backtrace_trade_log_path, self._backtrace_trade_log_filter)
        backtrace_flow_log_filter_lines = self.get_filter_lines(self._backtrace_flow_log_path, self._backtrace_flow_log_filter)
        print("===== CTP trade log content =====")
        print("\n".join(ctp_trade_log_filter_lines))
        print("===== Backtest trade log content =====")
        print("\n".join(backtrace_trade_log_filter_lines))
        print("===== Backtest flow log content =====")
        print("\n".join(backtrace_flow_log_filter_lines))



class CtpLiveVerify:
    def __init__(self):
        self._ctp_live_config = "/root/config/flow_strategy_new.json"
        self._ctp_live_data_dir = "/root/through/data/FlowStrategy"
        self._ctp_live_trade_log_dir = "/root/through/log"
        self._origin_hdf5_dir = "/root/.rqalpha/bundle"
        self._origin_hdf5_file_name = "futures_min.h5"
        self._output_file_name = "futures_min.h5"
        self._output_file_dir = None
        self._output_file_path = None
        self._backtrace_trades_list = []
        self._ctp_trades_list = []
        self._report_msg = []
        self._report_send_list = ["wzf_92@163.com"]
        self._valify_list = [
            {"trade_file_name":"i2105_trade.log", "data_file_name":"I88.csv"},
            {"trade_file_name":"j2105_trade.log", "data_file_name":"J88.csv"},
#            {"trade_file_name":"rb2105_trade.log", "data_file_name":"RB88.csv"},
#            {"trade_file_name":"ru2105_trade.log", "data_file_name":"RU88.csv"},
        ]
        self._init()


    def _init(self):
        self._output_file_dir = datetime.datetime.now().strftime("%Y-%m-%d")
        if os.path.exists(self._output_file_dir) is False:
            os.makedirs(self._output_file_dir)
        self._output_file_path = os.path.join(self._output_file_dir, self._output_file_name)
        self._live_cfg = parse_json(self._ctp_live_config)
        self._suite_test = unittest.TestSuite()


    def _init_contract(self, contract):
        self._contract_name =  contract["data_file_name"].split(".")[0]
        self._ctp_live_data_path = os.path.join(self._ctp_live_data_dir, contract["data_file_name"])
        self._ctp_live_trade_log_path = os.path.join(self._ctp_live_trade_log_dir, contract["trade_file_name"])
        self._output_file_dir_contract = os.path.join(self._output_file_dir, self._contract_name)
        if not os.path.exists(self._output_file_dir_contract):
            os.makedirs(self._output_file_dir_contract)
        self._backtrace_trade_log_path = os.path.join(self._output_file_dir_contract, "report", "trades.csv")
        self._ctp_live_trade_log_path = os.path.join(self._ctp_live_trade_log_dir, contract["trade_file_name"])


    def create_hdf5(self):
        kline2hdf5 = Kline2HDF5.Kline2HDF5(self._output_file_path)
        for v in self._valify_list:
            symbol = v["data_file_name"].split('.')[0]
            kline2hdf5.translate(os.path.join(self._ctp_live_data_dir, v["data_file_name"]), symbol)
        kline2hdf5.finished()
         

    def backup_origin_hdf5(self):
        old_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name)
        backup_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name + ".backup")
        try:
            os.rename(old_name, backup_name)
        except Exception as e:
            print(e)
            print('backup file fail')
            sys.exit(1)



    def move_test_hdf5(self):
        old_name = self._output_file_path
        new_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name)
        try:
            os.system('cp %s %s' % (old_name, new_name))
        except Exception as e:
            print(e)
            print('cp test file fail')
            sys.exit(1)


    def restore_origin_hdf5(self):
        old_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name)
        backup_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name + ".backup")
        try:
            os.rename(backup_name, old_name)
        except Exception as e:
            print(e)
            print('restore file fail')
            sys.exit(1)


    def parse_backtrace_trade_log(self, filter = None):
        self._backtrace_trades_list = []
        with open(self._backtrace_trade_log_path, 'r') as in_file:
            lines = in_file.readlines()
            for l in lines:
                if filter and not filter(l):
                    continue
                v = l.strip('\n').split(',')
                t = v[0]
                operation = "UNPARSED"
                if v[4] == "BUY":
                    if "OPEN" in v[5]:
                        operation = "OPEN_LONG"
                    elif "CLOSE" in v[5]:
                        operation = "CLOSE_SHORT"
                elif v[4] == "SELL":
                    if "OPEN" in v[5]:
                        operation = "OPEN_SHORT"
                    elif "CLOSE" in v[5]:
                        operation = "CLOSE_LONG"
                self._backtrace_trades_list.append(','.join([t, operation]))
        print("backtract_trade: %s" % str(self._backtrace_trades_list))


    def parse_ctplive_trade_log(self, filter = None):
        self._ctp_trades_list = []
        with open(self._ctp_live_trade_log_path, 'r') as in_file:
            lines = in_file.readlines()
            for l in lines:
                if filter and not filter(l):
                    continue
                v = l.strip('\n').split(',')
                t = datetime.datetime.strptime(v[0], "%Y-%m-%d %H:%M:%S")
                operation = "UNPARSED"
                if "OPEN_LONG" in v[3]:
                    operation = "OPEN_LONG"
                elif "CLOSE_LONG" in v[3]:
                    operation = "CLOSE_LONG"
                elif "OPEN_SHORT" in v[3]:
                    operation = "OPEN_SHORT"
                elif "CLOSE_SHORT" in v[3]:
                    operation = "CLOSE_SHORT"
                else:
                    continue
                self._ctp_trades_list.append(','.join([str(t), operation]))
        print("ctp_trade: %s" % str(self._ctp_trades_list))


    def update_config(self, contract):
        self._config['mod']['sys_analyser']['report_save_path'] = os.path.join(self._output_file_dir_contract, 'report')
        for live_contract in self._live_cfg["contracts"]:
            if live_contract["kline_file_path"] == self._ctp_live_data_path and live_contract["trade_log_path"] == self._ctp_live_trade_log_path:
                self._config["strategy"]["flow_through"]["contract"] = self._contract_name
                params = live_contract["strategy_params"]
                self._config["strategy"]["flow_through"]["open_long_threshold"] = params["threshold_open_long"]
                self._config["strategy"]["flow_through"]["close_long_threshold"] = params["threshold_close_long"]
                self._config["strategy"]["flow_through"]["open_short_threshold"] = params["threshold_open_short"]
                self._config["strategy"]["flow_through"]["close_short_threshold"] = params["threshold_close_short"]
                self._config["mod"]["stop_profit_loss"]["stop_profit"] = float(params["stop_profit"])
                self._config["mod"]["stop_profit_loss"]["stop_loss"] = abs(float(params["stop_loss"]))
                break

    def run_backtrace(self, config, strategy_file_path):
        self._config = config
        for contract in self._valify_list:
            self._init_contract(contract)
            self.update_config(contract)
            print("strategy_params: %s" % str(self._config))
            res = run_file(strategy_file_path, self._config)
            self.parse_backtrace_trade_log(backtrace_filter)
            self.parse_ctplive_trade_log(ctplive_filter)
            self.valify()


    def valify(self):
        ctp_surplus_list = []
        backtrace_surplus_list = []
        self._report_msg.append("========== {name} ==========".format(name=self._contract_name))
        for ctp_trade in self._ctp_trades_list:
            if ctp_trade not in self._backtrace_trades_list:
                ctp_surplus_list.append(ctp_trade)
        for backtrace_trade in self._backtrace_trades_list:
            if backtrace_trade not in self._ctp_trades_list:
                backtrace_surplus_list.append(ctp_trade)
        if not ctp_surplus_list and not backtrace_surplus_list:
            self._report_msg.append("{name} verified pass.".format(name=self._contract_name))
            return True
        self._report_msg.append("{name} verified faild, details:\n".format(name=self._contract_name))
        if ctp_surplus_list:
            self._report_msg.append("Found in the ctp live log, but not in the backtest log:")
            for ctp_trade in ctp_surplus_list:
                vars = ctp_trade.split(",")
                self._report_msg.append("[{time}] {operation}".format(time=vars[0], operation=vars[1]))
            self._report_msg.append("")
        if backtrace_surplus_list:
            self._report_msg.append("Found in the backtest log, but not in the ctp live log:\n")
            for backtrace_trade in backtrace_surplus_list:
                vars = backtrace_trade.split(",")
                self._report_msg.append("[{time}] {operation}".format(time=vars[0], operation=vars[1]))
            self._report_msg.append("")
        return False


    def report(self):
        msg = "\n".join(self._report_msg)
        mail_client = QqMail(self._report_send_list)
        mail_client.send_mail("Verification of CTP trades", msg)
        print(msg)

if __name__ == '__main__':
    config = {
      "base": {
        "start_date": "2020-01-01",
        "end_date": "2099-12-31",
        "frequency": "1m",
        "accounts": {
            "future": 100000
        }
      },
      "mod": {
        "sys_progress": {
          "enabled": True,
          "show": True
        },
        "sys_analyser": {
          "enabled": True
        },
        "stop_profit_loss": {
          "enabled": True
        },
        "factor_flow": {
          "enabled": True,
          "log_dir": "flow_report"
        }
      },
      "strategy": {
          "flow_through":
          {
              "contract": "I88",
              "open_long_threshold": "> 0.1",
              "close_long_threshold": "< 0.1",
              "open_short_threshold": "< -0.1",
              "close_short_threshold": "> -0.1",
          }
      }
    }
    strategy_file_path = "/root/projects/rqalpha/rqalpha/examples/strategy_flow.py"

    clv = CtpLiveVerify()
    clv.create_hdf5()
    clv.backup_origin_hdf5()
    try:
        clv.move_test_hdf5()
        clv.run_backtrace(config, strategy_file_path)
        clv.report()
    finally:
        clv.restore_origin_hdf5()

