# 这两个模块用于多线程并发
import concurrent.futures
import multiprocessing
import os
import copy
import glob
import pandas as pd
import random

from rqalpha import run

import logging
logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchRun:
    def __init__(self, contract_name, result_path):
        self._contract_name = contract_name
        self._result_path = result_path
        self._params_template = {}
        self._params_base_list = []
        self._params_list = []
        self._all_result_dict = {}
        self._filter_result_dict = {}
        self._init_params_template()
        self._init_params()

    def _init_params_template(self):
        self._params_template = {
              "base": {
                # 策略的路径，必须要有
                "strategy_file": "/root/projects/rqalpha/rqalpha/examples/strategy_flow.py",
                "start_date": "2015-01-01",
                "end_date": "2020-12-01",
                "frequency": "1m",
                "accounts": {
                    "future": 100000000
                }
              },
              "mod": {
                "sys_progress": {
                  "enabled": True,
                  "show": True
                },
                "sys_analyser": {
                  "enabled": True,
                  # 回测结果的保存路径，必须要有
                  "output_file": "/root/strategy_flow_through_results/I88.pkl"
                },
                "factor_flow": {
                  "enabled": True,
                },
                "force_close": {
                  "enabled": True,
                },
                "force_not_open": {
                  "enabled": True,
                },
                "stop_profit_loss": {
                  "enabled": True,
                  "stop_profit": 0.03,
                  "stop_loss": 0.03,
                }
              },
              "strategy": {
                  "flow_through":
                  {
                      "contract": self._contract_name,
                      # 遍历参数填充
                      "open_long_threshold": "> 0.5",
                      "close_long_threshold": "< 0.5",
                      "open_short_threshold": "< -0.5",
                      "close_short_threshold": "> -0.5",
                  }
              }
        }


    def _init_params(self):
        self._params_base_list = [
        # type 1
        {'open_long_threshold': '> 0.2', 'close_long_threshold': '< 0.2', 'open_short_threshold': '< -0.2', 'close_short_threshold': '> -0.2'},
        {'open_long_threshold': '> 0.5', 'close_long_threshold': '< 0.5', 'open_short_threshold': '< -0.5', 'close_short_threshold': '> -0.5'},
        {'open_long_threshold': '> 0.8', 'close_long_threshold': '< 0.8', 'open_short_threshold': '< -0.8', 'close_short_threshold': '> -0.8'},
        {'open_long_threshold': '> 0.2', 'close_long_threshold': '< 0.1', 'open_short_threshold': '< -0.2', 'close_short_threshold': '> -0.1'},
        {'open_long_threshold': '> 0.5', 'close_long_threshold': '< 0.4', 'open_short_threshold': '< -0.5', 'close_short_threshold': '> -0.4'},
        {'open_long_threshold': '> 0.8', 'close_long_threshold': '< 0.7', 'open_short_threshold': '< -0.8', 'close_short_threshold': '> -0.7'},
        {'open_long_threshold': '> 0.2', 'close_long_threshold': '< 0.3', 'open_short_threshold': '< -0.2', 'close_short_threshold': '> -0.3'},
        {'open_long_threshold': '> 0.5', 'close_long_threshold': '< 0.6', 'open_short_threshold': '< -0.5', 'close_short_threshold': '> -0.6'},
        {'open_long_threshold': '> 0.8', 'close_long_threshold': '< 0.9', 'open_short_threshold': '< -0.8', 'close_short_threshold': '> -0.9'},
        # type 2
        {'open_long_threshold': '> 0.2', 'close_long_threshold': '> 0.3', 'open_short_threshold': '< -0.2', 'close_short_threshold': '< -0.3'},
        {'open_long_threshold': '> 0.4', 'close_long_threshold': '> 0.5', 'open_short_threshold': '< -0.4', 'close_short_threshold': '< -0.5'},
        {'open_long_threshold': '> 0.6', 'close_long_threshold': '> 0.7', 'open_short_threshold': '< -0.6', 'close_short_threshold': '< -0.7'},
        {'open_long_threshold': '> 0.2', 'close_long_threshold': '> 0.4', 'open_short_threshold': '< -0.2', 'close_short_threshold': '< -0.4'},
        {'open_long_threshold': '> 0.4', 'close_long_threshold': '> 0.6', 'open_short_threshold': '< -0.4', 'close_short_threshold': '< -0.6'},
        {'open_long_threshold': '> 0.6', 'close_long_threshold': '> 0.8', 'open_short_threshold': '< -0.6', 'close_short_threshold': '< -0.8'},
        {'open_long_threshold': '> 0.2', 'close_long_threshold': '> 0.5', 'open_short_threshold': '< -0.2', 'close_short_threshold': '< -0.5'},
        {'open_long_threshold': '> 0.4', 'close_long_threshold': '> 0.7', 'open_short_threshold': '< -0.4', 'close_short_threshold': '< -0.7'},
        {'open_long_threshold': '> 0.6', 'close_long_threshold': '> 0.9', 'open_short_threshold': '< -0.6', 'close_short_threshold': '< -0.9'},
        # type 3
        {'open_long_threshold': '< -0.2', 'close_long_threshold': '> -0.2', 'open_short_threshold': '> 0.2', 'close_short_threshold': '< 0.2'},
        {'open_long_threshold': '< -0.5', 'close_long_threshold': '> -0.5', 'open_short_threshold': '> 0.5', 'close_short_threshold': '< 0.5'},
        {'open_long_threshold': '< -0.8', 'close_long_threshold': '> -0.8', 'open_short_threshold': '> 0.8', 'close_short_threshold': '< 0.8'},
        {'open_long_threshold': '< -0.2', 'close_long_threshold': '> -0.1', 'open_short_threshold': '> 0.2', 'close_short_threshold': '< 0.1'},
        {'open_long_threshold': '< -0.5', 'close_long_threshold': '> -0.4', 'open_short_threshold': '> 0.5', 'close_short_threshold': '< 0.4'},
        {'open_long_threshold': '< -0.8', 'close_long_threshold': '> -0.7', 'open_short_threshold': '> 0.8', 'close_short_threshold': '< 0.7'},
        {'open_long_threshold': '< -0.2', 'close_long_threshold': '> -0.3', 'open_short_threshold': '> 0.2', 'close_short_threshold': '< 0.3'},
        {'open_long_threshold': '< -0.5', 'close_long_threshold': '> -0.6', 'open_short_threshold': '> 0.5', 'close_short_threshold': '< 0.6'},
        {'open_long_threshold': '< -0.8', 'close_long_threshold': '> -0.9', 'open_short_threshold': '> 0.8', 'close_short_threshold': '< 0.9'},
        # type 4
        {'open_long_threshold': '< -0.2', 'close_long_threshold': '< -0.3', 'open_short_threshold': '> 0.2', 'close_short_threshold': '> 0.3'},
        {'open_long_threshold': '< -0.4', 'close_long_threshold': '< -0.5', 'open_short_threshold': '> 0.4', 'close_short_threshold': '> 0.5'},
        {'open_long_threshold': '< -0.6', 'close_long_threshold': '< -0.7', 'open_short_threshold': '> 0.6', 'close_short_threshold': '> 0.7'},
        {'open_long_threshold': '< -0.2', 'close_long_threshold': '< -0.4', 'open_short_threshold': '> 0.2', 'close_short_threshold': '> 0.4'},
        {'open_long_threshold': '< -0.4', 'close_long_threshold': '< -0.6', 'open_short_threshold': '> 0.4', 'close_short_threshold': '> 0.6'},
        {'open_long_threshold': '< -0.6', 'close_long_threshold': '< -0.8', 'open_short_threshold': '> 0.6', 'close_short_threshold': '> 0.8'},
        {'open_long_threshold': '< -0.2', 'close_long_threshold': '< -0.5', 'open_short_threshold': '> 0.2', 'close_short_threshold': '> 0.5'},
        {'open_long_threshold': '< -0.4', 'close_long_threshold': '< -0.7', 'open_short_threshold': '> 0.4', 'close_short_threshold': '> 0.7'},
        {'open_long_threshold': '< -0.6', 'close_long_threshold': '< -0.9', 'open_short_threshold': '> 0.6', 'close_short_threshold': '> 0.9'}
        ]
        p = self._params_template
        for it in self._params_base_list:
            for k,v in it.items():
                p['strategy']['flow_through'][k] = v
            ol_v = p['strategy']['flow_through']['open_long_threshold'].split(' ')
            cl_v = p['strategy']['flow_through']['close_long_threshold'].split(' ')
            if ol_v[0] is '>' and cl_v[0] is '<':
                run_type = 1
            elif ol_v[0] is '>' and cl_v[0] is '>':
                run_type = 2
            elif ol_v[0] is '<' and cl_v[0] is '>':
                run_type = 3
            elif ol_v[0] is '<' and cl_v[0] is '<':
                run_type = 4
            else:
                assert False
            it1 = ol_v[1].replace('-', '')
            it2 = cl_v[1].replace('-', '')
            stop_profit = p['mod']['stop_profit_loss']['stop_profit']
            stop_loss = p['mod']['stop_profit_loss']['stop_loss']
            file_name = '{contract_name}-{run_type}-{it1}-{it2}-{stop_profit}-{stop_loss}.pkl'.format(contract_name=self._contract_name, run_type=run_type, it1=it1, it2=it2, stop_profit=stop_profit, stop_loss=stop_loss)
            p['mod']['sys_analyser']['output_file'] = os.path.join(self._result_path, file_name)
            self._params_list.append(copy.deepcopy(p))

    def _read_pickle(self, key):
        file_name = os.path.join(self._result_path, key + '.pkl')
        v = key.split('-')
        contract = v[0]
        strategy_type = v[1]
        threshold_1 = v[2]
        threshold_2 = v[3]
        stop_profit = v[4]
        stop_loss = v[5]
        result_dict = pd.read_pickle(file_name)
        summary = result_dict["summary"]
        summary["stop_profit"] = str(round(float(stop_profit),4))
        summary["stop_loss"] = str(round(float(stop_loss),4))
        if strategy_type == "1":
            summary["open_long_threshold"] = "> %s" % threshold_1
            summary["close_long_threshold"] = "< %s" % threshold_1
            summary["open_short_threshold"] = "< -%s" % threshold_2
            summary["close_short_threshold"] = "> -%s" % threshold_2
        elif strategy_type == "2":
            summary["open_long_threshold"] = "> %s" % threshold_1
            summary["close_long_threshold"] = "> %s" % threshold_1
            summary["open_short_threshold"] = "< -%s" % threshold_2
            summary["close_short_threshold"] = "< -%s" % threshold_2
        elif strategy_type == "3":
            summary["open_long_threshold"] = "< -%s" % threshold_1
            summary["close_long_threshold"] = "> -%s" % threshold_1
            summary["open_short_threshold"] = "> %s" % threshold_2
            summary["close_short_threshold"] = "< %s" % threshold_2
        elif strategy_type == "4":
            summary["open_long_threshold"] = "< -%s" % threshold_1
            summary["close_long_threshold"] = "< -%s" % threshold_1
            summary["open_short_threshold"] = "> %s" % threshold_2
            summary["close_short_threshold"] = "> %s" % threshold_2
        return summary


    def _read_summary(self, contract_name):
        file_list = glob.glob(os.path.join(self._result_path, contract_name + '*'))
        for file_name in file_list:
            basename = os.path.basename(file_name)
            key = basename.replace(".pkl", "")
            summary = self._read_pickle(key)
            self._all_result_dict[key] = summary

    def _calc_score(self, params):
#        return round(params['annualized_returns']/params['max_drawdown'], 4) if params['max_drawdown'] > 0.000001 else 0
        return round(params['total_returns']/params['max_drawdown'], 4) if params['max_drawdown'] > 0.000001 else 0

    def _filter_result(self):
        scores = {}
        for k,v in self._all_result_dict.items():
            scores[k] = self._calc_score(v)
        sort_scores = sorted(scores.items(), key=lambda i: i[1], reverse=True)
        res_type = []
        res_cnt = 0
        print(sort_scores)
        for k,v in sort_scores:
            if res_cnt >= 3:
                break
            if v < 1:
                continue
            cur_type = k.split('-')[1]
            if cur_type in res_type:
                continue
            self._filter_result_dict[k] = self._all_result_dict[k]
            res_type.append(cur_type)
            res_cnt += 1
        print(self._filter_result_dict.items())
#        exit(0)

    def _update_params_by_key(self, params, key):
        v = key.split('-')
        contract = v[0]
        strategy_type = v[1]
        threshold_1 = v[2]
        threshold_2 = v[3]
        stop_profit = v[4]
        stop_loss = v[5]
        res = copy.deepcopy(params)
        res['mod']['stop_profit_loss']['stop_profit'] = round(float(stop_profit),4)
        res['mod']['stop_profit_loss']["stop_loss"] = round(float(stop_loss),4)
        if strategy_type == "1":
            res['strategy']['flow_through']["open_long_threshold"] = "> %s" % threshold_1
            res['strategy']['flow_through']["close_long_threshold"] = "< %s" % threshold_1
            res['strategy']['flow_through']["open_short_threshold"] = "< -%s" % threshold_2
            res['strategy']['flow_through']["close_short_threshold"] = "> -%s" % threshold_2
        elif strategy_type == "2":
            res['strategy']['flow_through']["open_long_threshold"] = "> %s" % threshold_1
            res['strategy']['flow_through']["close_long_threshold"] = "> %s" % threshold_1
            res['strategy']['flow_through']["open_short_threshold"] = "< -%s" % threshold_2
            res['strategy']['flow_through']["close_short_threshold"] = "< -%s" % threshold_2
        elif strategy_type == "3":
            res['strategy']['flow_through']["open_long_threshold"] = "< -%s" % threshold_1
            res['strategy']['flow_through']["close_long_threshold"] = "> -%s" % threshold_1
            res['strategy']['flow_through']["open_short_threshold"] = "> %s" % threshold_2
            res['strategy']['flow_through']["close_short_threshold"] = "< %s" % threshold_2
        elif strategy_type == "4":
            res['strategy']['flow_through']["open_long_threshold"] = "< -%s" % threshold_1
            res['strategy']['flow_through']["close_long_threshold"] = "< -%s" % threshold_1
            res['strategy']['flow_through']["open_short_threshold"] = "> %s" % threshold_2
            res['strategy']['flow_through']["close_short_threshold"] = "> %s" % threshold_2
        file_name = '{contract_name}-{run_type}-{it1}-{it2}-{stop_profit}-{stop_loss}.pkl'.format(contract_name=contract, run_type=strategy_type, it1=threshold_1, it2=threshold_2, stop_profit=stop_profit, stop_loss=stop_loss)
        res['mod']['sys_analyser']['output_file'] = os.path.join(self._result_path, file_name)
        return res

    def _run_task(self, key, params, disable_output=False):
        logger.info("run %s, %s" % (key, params))
        if disable_output:
            params['mod']['sys_analyser']['output_file'] = None
        run(params)
        if disable_output:
            return
        summary = self._read_pickle(key)
        self._all_result_dict[key] = summary

    def _foreach_threshold_down(self, init_key, init_score, step, pos, limit):
        res_score = init_score
        v = init_key.split('-')
        it = float(v[pos+1])
        res = False
        res_key = None
        while it >= limit:
            it -= step
            v[pos+1] = str(round(it, 4))
            new_key = '-'.join(v)
            if self._all_result_dict.__contains__(new_key) is False:
                new_params = self._update_params_by_key(self._params_template, new_key)
                self._run_task(new_key, new_params)
            new_score = self._calc_score(self._all_result_dict[new_key])
            logger.info("search %s: %f" % (new_key, new_score))
            if new_score <= res_score:
                return res, res_key, res_score
            res = True
            res_key = new_key
            res_score = new_score
        return res, res_key, res_score

    def _foreach_threshold_up(self, init_key, init_score, step, pos, limit):
        res_score = init_score
        v = init_key.split('-')
        it = float(v[pos+1])
        res = False
        res_key = None
        while it <= limit:
            it += step
            v[pos+1] = str(round(it, 4))
            new_key = '-'.join(v)
            if self._all_result_dict.__contains__(new_key) is False:
                new_params = self._update_params_by_key(self._params_template, new_key)
                self._run_task(new_key, new_params)
            new_score = self._calc_score(self._all_result_dict[new_key])
            logger.info("search %s: %f" % (new_key, new_score))
            if new_score <= res_score:
                return res, res_key, res_score
            res = True
            res_key = new_key
            res_score = new_score
        return res, res_key, res_score


    def _foreach_threshold_one_round(self, init_key, init_score, step):
        logger.info("one_round init %s, %f" % (init_key, init_score))
        cur_key = init_key
        cur_score = init_score

        for pos in range(1,3):
            res_down, new_key_down, new_score_down = self._foreach_threshold_down(copy.deepcopy(cur_key), cur_score, step, pos, 0.1)
            res_up, new_key_up, new_score_up = self._foreach_threshold_up(copy.deepcopy(cur_key), cur_score, step, pos, 0.9)
            logger.info("return pos %d: down %s, %f; up %s, %f" % (pos, new_key_down, new_score_down, new_key_up, new_score_up))
            if res_down and res_up:
                if new_score_down > new_score_up:
                    cur_key = new_key_down
                    cur_score = new_score_down
                else:
                    cur_key = new_key_up
                    cur_score = new_score_up
            elif res_down:
                cur_key = new_key_down
                cur_score = new_score_down
            elif res_up:
                cur_key = new_key_up
                cur_score = new_score_up

        logger.info("one_round result %s, %f" % (cur_key, cur_score))
        return cur_key, cur_score


    def _foreach_threshold(self, init_key):
        step = 0.05
        if self._all_result_dict.__contains__(init_key) is False:
            init_params = self._update_params_by_key(self._params_template, init_key)
            self._run_task(init_key, init_params)
        init_score = self._calc_score(self._all_result_dict[init_key])
        cur_key = init_key
        cur_score = init_score
        while True:
            new_key, new_score = self._foreach_threshold_one_round(cur_key, cur_score, step)
            if new_key == cur_key:
                return new_key, new_score
            cur_key = new_key
            cur_score = new_score

    def _foreach_stop_profit_loss_one_round(self, init_key, init_score, step):
        logger.info("one_round init %s, %f" % (init_key, init_score))
        cur_key = init_key
        cur_score = init_score

        for pos in range(3,5):
            res_down, new_key_down, new_score_down = self._foreach_threshold_down(copy.deepcopy(cur_key), cur_score, step, pos, 0.01)
            res_up, new_key_up, new_score_up = self._foreach_threshold_up(copy.deepcopy(cur_key), cur_score, step, pos, 0.1)
            logger.info("return pos %d: down %s, %f; up %s, %f" % (pos, new_key_down, new_score_down, new_key_up, new_score_up))
            if res_down and res_up:
                if new_score_down > new_score_up:
                    cur_key = new_key_down
                    cur_score = new_score_down
                else:
                    cur_key = new_key_up
                    cur_score = new_score_up
            elif res_down:
                cur_key = new_key_down
                cur_score = new_score_down
            elif res_up:
                cur_key = new_key_up
                cur_score = new_score_up

        logger.info("one_round result %s, %f" % (cur_key, cur_score))
        return cur_key, cur_score



    def _foreach_stop_profit_loss(self, init_key):
        step = 0.005
        if self._all_result_dict.__contains__(init_key) is False:
            init_params = self._update_params_by_key(self._params_template, init_key)
            self._run_task(init_key, init_params)
        init_score = self._calc_score(self._all_result_dict[init_key])
        cur_key = init_key
        cur_score = init_score
        while True:
            new_key, new_score = self._foreach_stop_profit_loss_one_round(cur_key, cur_score, step)
            if new_key == cur_key:
                return new_key, new_score
            cur_key = new_key
            cur_score = new_score

    def _check_key(self, key):
        d_t1 = random.uniform(-0.05, 0.05)
        d_t2 = random.uniform(-0.05, 0.05)
        d_sp = random.uniform(-0.005, 0.005)
        d_sl = random.uniform(-0.005, 0.005)
        v = key.split('-')
        contract = v[0]
        strategy_type = v[1]
        threshold_1 = round(float(v[2]) + d_t1, 4)
        threshold_2 = round(float(v[3]) + d_t2, 4)
        stop_profit = round(float(v[4]) + d_sp, 4)
        stop_loss = round(float(v[5]) + d_sl, 4)
        new_key = '%s-%s-%f-%f-%f-%f' % (contract, strategy_type, threshold_1, threshold_2, stop_profit, stop_loss)
        logger.info("new_key %s" % new_key)
        new_params = self._update_params_by_key(self._params_template, new_key)
        self._run_task(new_key, new_params, disable_output=True)
        # logger.info(self._all_result_dict[new_key])

        
    def update(self):
        for k,v in self._filter_result_dict.items():
#            if k != 'AL88-1-0.15-0.2-0.025-0.03':
#                continue
            cur_key = k
            while True:
                init_key = cur_key
                cur_key, cur_score = self._foreach_threshold(cur_key)
                cur_key, cur_score = self._foreach_stop_profit_loss(cur_key)
                if init_key == cur_key:
                    logger.info("final res %s, %f" % (cur_key, cur_score))
#                    check_res = self._check_key(cur_key)
                    break


if __name__ == '__main__':
#    contract_list = ['I88', 'J88']
#    contract_list = ['IH88','IC88','IF88','AL88','AU88','CU88','RB88','RU88','SC88','SM88','ZN88']
#    contract_list = ['AL88','AU88','CU88','RB88','RU88','SC88','SM88','ZN88','IC88','IF88']
#    contract_list = ['AU88','CU88','RB88','RU88','SC88','SM88','ZN88','IC88','IF88']
#    contract_list = ['CU88','RB88','RU88','SC88','SM88','ZN88','IC88','IF88']
#    contract_list = ['RU88','SC88','SM88','ZN88','IC88','IF88']
#    contract_list = ['AU88','CU88','RB88','RU88','SC88','SM88','ZN88','IC88','IF88']
#    contract_list = ['AU88','CU88','RB88','RU88','SC88','SM88','ZN88','IC88','IF88']
#    contract_list = ['IF88','IC88','IH88']
#    contract_list = ['IF88']
#    contract_list = ['IH88','IC88','IF88','AL88','CU88','RB88','RU88','SC88','SM88','ZN88']
    contract_list = ['RB88','RU88','SC88','SM88','ZN88']
    for contract_name in contract_list:
        output_path = os.path.join('/root/strategy_flow_through_results', contract_name)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        br = BatchRun(contract_name, output_path)
        tasks = br._params_list

#        with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
#            all_task = [executor.submit(run, task) for task in tasks]
#        concurrent.futures.wait(all_task)

        br._read_summary(contract_name)
        br._filter_result()
        print(len(br._filter_result_dict.keys()), br._filter_result_dict)
        br.update()
#        break

