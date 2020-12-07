from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT
from collections import defaultdict
import numpy as np
import os

class CalcFlowFactor(AbstractMod):
    def __init__(self):
        self._log_dir = None
        self._log_file = defaultdict(lambda: None)
        self._save_flow_value_cnt = 2000
        self._save_flow_value_list = defaultdict(list)
        self._save_flow_value_list_cur_index = defaultdict(lambda: -1)
        self._save_flow_value_enable = defaultdict(bool)
        self._kline_bar_cnt = 240
        self._kline_bar_inflow = defaultdict(list)
        self._kline_bar_inflow_total = defaultdict(float)
        self._kline_bar_volume = defaultdict(list)
        self._kline_bar_volume_total = defaultdict(float)
        self._kline_bar_cur_index = defaultdict(lambda: -1)
        self._kline_bar_enable = defaultdict(bool)
        self._max_flow = defaultdict(float)
        self._cur_flow = defaultdict(float)
        self._cur_flow_ratio = defaultdict(float)

    def start_up(self, env, mod_config):
        self._kline_bar_cnt = mod_config.slice
        self._save_flow_value_cnt = mod_config.size
        if "log_dir" in mod_config.keys():
            self._log_dir = mod_config.log_dir
        env.event_bus.add_listener(EVENT.PRE_BAR, self._update_flow)

    def tear_down(self, success, exception=None):
        for f in self._log_file.values():
            if f:
                f.close()

    def _update_max_flow(self, c, new_flow, del_flow):
        assert del_flow <= self._max_flow[c]
        if del_flow == self._max_flow[c]:
            self._max_flow[c] = max(self._save_flow_value_list[c])
            return
        if new_flow > self._max_flow[c]:
            self._max_flow[c] = new_flow
        return

    def _update_flow_one_contract(self, c, bar):
        bar_index = self._kline_bar_cur_index[c] = (self._kline_bar_cur_index[c] + 1) % self._kline_bar_cnt
        inflow = bar.close * bar.volume
        if not self._kline_bar_enable[c]:
            self._kline_bar_inflow[c].append(inflow)
            self._kline_bar_volume[c].append(bar.volume)
            self._kline_bar_inflow_total[c] += inflow
            self._kline_bar_volume_total[c] += bar.volume
            if bar_index == self._kline_bar_cnt - 1:
                self._kline_bar_enable[c] = True
        else:
            last_inflow = self._kline_bar_inflow[c][bar_index]
            last_volume = self._kline_bar_volume[c][bar_index]
            self._kline_bar_inflow[c][bar_index] = inflow
            self._kline_bar_volume[c][bar_index] = bar.volume
            self._kline_bar_inflow_total[c] = self._kline_bar_inflow_total[c] - last_inflow + inflow
            self._kline_bar_volume_total[c] = self._kline_bar_volume_total[c] - last_volume + bar.volume
#        print("%s: inflow_list %s, volume list %s" % (str(bar.datetime), str(self._kline_bar_inflow[c]), str(self._kline_bar_volume[c])))
        if not self._kline_bar_enable[c]:
            return False
        outflow = bar.close * self._kline_bar_volume_total[c]
        flow = self._cur_flow[c] = self._kline_bar_inflow_total[c] - outflow
        abs_flow = abs(flow)
        flow_index = self._save_flow_value_list_cur_index[c] = (self._save_flow_value_list_cur_index[c] + 1) \
                                                               % self._save_flow_value_cnt
        if not self._save_flow_value_enable[c]:
            self._save_flow_value_list[c].append(abs_flow)
            if flow_index == self._save_flow_value_cnt - 1:
                self._save_flow_value_enable[c] = True
            self._update_max_flow(c, abs_flow, 0)
        else:
            del_flow = self._save_flow_value_list[c][flow_index]
            self._save_flow_value_list[c][flow_index] = abs_flow
            self._update_max_flow(c, abs_flow, del_flow)
        if not self._save_flow_value_enable[c]:
            return False
        self._cur_flow_ratio[c] = round(self._cur_flow[c] / self._max_flow[c], 6)
        if not self._log_dir:
            return True
        if not self._log_file[c]:
            path = os.path.join(self._log_dir, c + '_flow.csv')
            self._log_file[c] = open(path, 'w')
        msg = "%s,%s" % (str(bar.datetime), self._cur_flow_ratio[c])
        self._log_file[c].write(msg + "\n")
        return True

    def _update_flow(self, event):
        contract_list = list(event.bar_dict.keys())
        for contract in contract_list:
            event.bar_dict[contract].flow_ratio = np.nan
            if event.bar_dict[contract].isnan:
                continue
            if self._update_flow_one_contract(contract, event.bar_dict[contract]):
                event.bar_dict[contract].flow_ratio = self._cur_flow_ratio[contract]
        pass
        # print("call _calc_flow")
        # if event.bar_dict._frequency != "1m":
        #     return
        # if len(self._kline_bar) < self._kline_bar_cnt:
        #     self._kline_bar.append(event.)
