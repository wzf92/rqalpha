import Kline2HDF5
import HDF5Reader
import sys
import os
import datetime
import json
from rqalpha import run_file

def parse_json(cfg_name):
    try:
        f = open(cfg_name, 'r')
    except IOError:
        print("Error: open configuration file \"%s\" failed" % cfg_name)
        exit(1)
    return json.loads(f.read())

def ctplive_filter(line):
    # today = datetime.datetime.now().strftime("%Y-%m-%d")
    today = "2020-12-14"
    return today in line


def backtrace_filter(line):
    # today = datetime.datetime.now().strftime("%Y-%m-%d")
    today = "2020-12-14"
    return today in line


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
        self._valify_list = [
            {"trade_file_name":"i2101_trade.log", "data_file_name":"I88.csv"},
#            {"trade_file_name":"i2105_trade.log", "data_file_name":"I88.csv"},
#            {"trade_file_name":"j2105_trade.log", "data_file_name":"J88.csv"},
#            {"trade_file_name":"rb2105_trade.log", "data_file_name":"RB88.csv"},
#            {"trade_file_name":"ru2105_trade.log", "data_file_name":"RU88.csv"},
        ]


    def create_hdf5(self):
        self._output_file_dir = datetime.datetime.now().strftime("%Y-%m-%d")
        if os.path.exists(self._output_file_dir) is False:
            os.makedirs(self._output_file_dir)
        self._output_file_path = os.path.join(self._output_file_dir, self._output_file_name)
        kline2hdf5 = Kline2HDF5.Kline2HDF5(self._output_file_path)
        for v in self._valify_list:
            symbol = v["data_file_name"].split('.')[0]
            kline2hdf5.translate(os.path.join(self._ctp_live_data_dir, v["data_file_name"]), symbol)
        kline2hdf5.finished()
         
        #reader = HDF5Reader.HDF5Reader()
        #reader.read(output_file_name, "I88")


    def backup_origin_hdf5(self):
        old_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name)
        backup_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name + ".backup")
        try:
            os.rename(old_name, backup_name)
        except Exception as e:
            print(e)
            print('backup file fail')
            sys.exit(1)
        else:
            print('backup file success')


    def move_test_hdf5(self):
        old_name = self._output_file_path
        new_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name)
        try:
            # os.rename(old_name, new_name)
            os.system('cp %s %s' % (old_name, new_name))
        except Exception as e:
            print(e)
            print('cp test file fail')
            sys.exit(1)
        else:
            print('cp test file success')


    def restore_origin_hdf5(self):
        old_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name)
        backup_name = os.path.join(self._origin_hdf5_dir, self._origin_hdf5_file_name + ".backup")
        try:
            os.rename(backup_name, old_name)
        except Exception as e:
            print(e)
            print('restore file fail')
            sys.exit(1)
        else:
            print('restore file success')


    def parse_backtrace_trade_log(self, filter = None):
        self._backtrace_trades_list = []
        in_file_path = os.path.join(self._output_file_dir, "report", "trades.csv")
        with open(in_file_path, 'r') as in_file:
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


    def parse_ctplive_trade_log(self, contract, filter = None):
        self._ctp_trades_list = []
        in_file_path = os.path.join(self._ctp_live_trade_log_dir, contract["trade_file_name"])
        with open(in_file_path, 'r') as in_file:
            lines = in_file.readlines()
            for l in lines:
                if filter and not filter(l):
                    continue
                v = l.strip('\n').split(',')
                t = datetime.datetime.strptime(v[0], "%Y-%m-%d %H:%M:%S")
                t = t - datetime.timedelta(minutes = 1)
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
        contract_name =  contract["data_file_name"].split(".")[0]
        ctp_live_data_path = os.path.join(self._ctp_live_data_dir, contract["data_file_name"])
        ctp_live_trade_log_path = os.path.join(self._ctp_live_trade_log_dir, contract["trade_file_name"])
        print(ctp_live_data_path)
        print(ctp_live_trade_log_path)
        for live_contract in self._live_cfg["contracts"]:
            print(live_contract["kline_file_path"])
            print(live_contract["trade_log_path"])
            if live_contract["kline_file_path"] == ctp_live_data_path and live_contract["trade_log_path"] == ctp_live_trade_log_path:
                self._config["strategy"]["flow_through"]["contract"] = contract_name
                params = live_contract["strategy_params"]
                self._config["strategy"]["flow_through"]["open_long_threshold"] = params["threshold_open_long"]
                self._config["strategy"]["flow_through"]["close_long_threshold"] = params["threshold_close_long"]
                self._config["strategy"]["flow_through"]["open_short_threshold"] = params["threshold_open_short"]
                self._config["strategy"]["flow_through"]["close_short_threshold"] = params["threshold_close_short"]
                self._config["mod"]["stop_profit_loss"]["stop_profit"] = float(params["stop_profit"])
                self._config["mod"]["stop_profit_loss"]["stop_loss"] = abs(float(params["stop_loss"]))
                break

    def run_backtrace(self, config, strategy_file_path):
        self._live_cfg = parse_json(self._ctp_live_config)
        self._config = config
        self._config['mod']['sys_analyser']['report_save_path'] = os.path.join(self._output_file_dir, 'report')
        for contract in self._valify_list:
            self.update_config(contract)
            print("strategy_params: %s" % str(self._config))
            res = run_file(strategy_file_path, self._config)
            self.parse_backtrace_trade_log(backtrace_filter)
            self.parse_ctplive_trade_log(contract, ctplive_filter)



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
    finally:
        clv.restore_origin_hdf5()

