from rqalpha.interface import AbstractMod
from rqalpha.apis import *
from rqalpha.events import EVENT
from collections import defaultdict
import datetime
import os


class StopProfitLoss(AbstractMod):
    def __init__(self):
        self._log_dir = None
        self._log_file = defaultdict(lambda: None)
        self._stop_profit = None
        self._stop_loss = None

    def start_up(self, env, mod_config):
        if "log_dir" in mod_config.keys():
            self._log_dir = mod_config.log_dir
            if os.path.exists(self._log_dir) is False:
                os.makedirs(self._log_dir)
        self._stop_profit = mod_config.stop_profit
        self._stop_loss = mod_config.stop_loss
#        env.event_bus.add_listener(EVENT.BAR, self._check_force_close)
        env.event_bus.prepend_listener(EVENT.BAR, self._stop_profit_loss)

    def tear_down(self, success, exception=None):
        for f in self._log_file.values():
            if f:
                f.close()

    def _stop_profit_loss(self, event):
        contract_list = list(event.bar_dict.keys())
        for contract in contract_list:
            event.bar_dict[contract].stop_profit = False
            event.bar_dict[contract].stop_loss = False
            contract_list = list(event.bar_dict.keys())
        for contract in contract_list:
            long_positions = get_position(contract, POSITION_DIRECTION.LONG)
            short_positions = get_position(contract, POSITION_DIRECTION.SHORT)
            if long_positions.quantity == 0 and short_positions.quantity == 0:
                continue
                # order_to(contract, 0)
            if long_positions.pnl_ratio >= self._stop_profit or short_positions.pnl_ratio >= self._stop_profit:
                event.bar_dict[contract].stop_profit = True
            elif long_positions.pnl_ratio <= -self._stop_loss or short_positions.pnl_ratio <= -self._stop_loss:
                event.bar_dict[contract].stop_loss = True
            if not self._log_dir:
                continue
            if not self._log_file[contract]:
                path = os.path.join(self._log_dir, contract + '_stop_profit_loss.csv')
                self._log_file[contract] = open(path, 'w')
            cur_time = event.calendar_dt
            if event.bar_dict[contract].stop_profit:
                msg = "%s,%s" % (str(cur_time), "STOP_PROFIT")
                self._log_file[contract].write(msg + "\n")
            elif event.bar_dict[contract].stop_loss:
                msg = "%s,%s" % (str(cur_time), "STOP_LOSS")
                self._log_file[contract].write(msg + "\n")
            # return True
        return
        # print("call _calc_flow")
        # if event.bar_dict._frequency != "1m":
        #     return
        # if len(self._kline_bar) < self._kline_bar_cnt:
        #     self._kline_bar.append(event.)
