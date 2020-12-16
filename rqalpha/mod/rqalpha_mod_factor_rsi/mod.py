from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT
from collections import defaultdict
import numpy as np
import os

class CalcRsiFactor(AbstractMod):
    def __init__(self):
        self._log_dir = None
        self._log_file = defaultdict(lambda: None)
        self._kline_bar_cnt = 14
        self._start_index = defaultdict(bool) 
        self._kline_bar_cur_index = defaultdict(lambda: -1)
        self._kline_bar_enable = defaultdict(bool)
        self._max_rsi = defaultdict(float)
        self._cur_rsi = defaultdict(float)
        self._upavg = defaultdict(float)
        self._downavg = defaultdict(float)
        self._last_price = defaultdict(float)
        self._kline_bar_diff_price = defaultdict(list)

    def start_up(self, env, mod_config):
        self._kline_bar_cnt = mod_config.slice
        #self._save_flow_value_cnt = mod_config.size
        if "log_dir" in mod_config.keys():
            self._log_dir = mod_config.log_dir
        env.event_bus.add_listener(EVENT.PRE_BAR, self._update_rsi)

    def tear_down(self, success, exception=None):
        for f in self._log_file.values():
            if f:
                f.close()

    def _update_rsi_one_contract(self, c, bar):
        bar_index = self._kline_bar_cur_index[c] = (self._kline_bar_cur_index[c] + 1) % self._kline_bar_cnt
        if not self._start_index[c]:
            self._last_price[c] = bar.close
            self._kline_bar_diff_price[c].append(0)
            self._start_index[c] = True
            return False
        diff_price = bar.close-self._last_price[c]
        if not self._kline_bar_enable[c]:
            self._kline_bar_diff_price[c].append(diff_price)
            if diff_price >= 0:
                self._upavg[c] += diff_price
            else:
                self._downavg[c] += abs(diff_price)
            self._last_price[c] = bar.close
            if bar_index == self._kline_bar_cnt - 1:
                self._kline_bar_enable[c] = True
        else:
            self._last_price[c] = bar.close
            last_diff_price = self._kline_bar_diff_price[c][bar_index]
            self._kline_bar_diff_price[c][bar_index] = diff_price
            if diff_price >= 0:
                self._upavg[c] += diff_price
            else:
                self._downavg[c] += abs(diff_price)
            if last_diff_price >= 0:
                self._upavg[c] -= last_diff_price
            else:
                self._downavg[c] -= abs(last_diff_price)
                
        if not self._kline_bar_enable[c]:
            return False
        
        if self._downavg[c] == 0 and self._upavg[c] != 0:
            rsi = 100
        elif self._downavg[c] == 0 and self._upavg[c] == 0:
            rsi = 50
        else:
            rs = self._upavg[c]/self._downavg[c]
            rsi = 100 - 100/(1+rs)
        self._cur_rsi[c] = rsi
        if not self._log_dir:
            return True
        if not self._log_file[c]:
            path = os.path.join(self._log_dir, c + '_rsi.csv')
            self._log_file[c] = open(path, 'w')
        msg = "%s,%s" % (str(bar.datetime), self._cur_rsi[c])
        self._log_file[c].write(msg + "\n")
        return True

    def _update_rsi(self, event):
        contract_list = list(event.bar_dict.keys())
        for contract in contract_list:
            event.bar_dict[contract].rsi = np.nan
            if event.bar_dict[contract].isnan:
                continue
            if self._update_rsi_one_contract(contract, event.bar_dict[contract]):
                event.bar_dict[contract].rsi = self._cur_rsi[contract]
        pass
        # print("call _calc_flow")
        # if event.bar_dict._frequency != "1m":
        #     return
        # if len(self._kline_bar) < self._kline_bar_cnt:
        #     self._kline_bar.append(event.)
