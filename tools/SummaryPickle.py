import os
import sys
import glob
import pymongo
import datetime
import pandas as pd

# 这个路径要和上面的"output_file"对应
#for name in glob.glob("/root/projects/rqalpha/results/*.pkl"):

def _calc_score(params):
    dt_start = datetime.datetime.strptime(params['start_date'], '%Y-%m-%d')
    dt_end = datetime.datetime.strptime(params['end_date'], '%Y-%m-%d')
    days = (dt_end - dt_start).days
    trades_per_day = float(params['trades_cnt']) / days
    if trades_per_day < 0.05:
        return -1
    return round(params['total_returns']/params['max_drawdown'], 4) if params['max_drawdown'] > 0.000001 else 0

output_file = None
if len(sys.argv) > 1:
    output_file = open(sys.argv[2], 'w')
    output_file.write('contract_name,backtest_time,bk,sp,sk,bp,stop_profit,stop_loss,score,annualized_returns,total_returns,max_drawdown,sharpe,trades_cnt\n')

for name in glob.glob(sys.argv[1]):
    file_name = os.path.basename(name).replace('.pkl', '')
    result_dict = pd.read_pickle(name)
    # summary即回测报告中的summary.csv中的内容
    summary = result_dict["summary"]
    trades = result_dict["trades"]

    v = file_name.split('-')
    contract_name = v[0]
    strategy_type = v[1]
    if strategy_type == '1':
        bk = '> ' + v[2]
        sp = '< ' + v[3]
        sk = '< -' + v[2]
        bp = '> -' + v[3]
    elif strategy_type == '2':
        bk = '> ' + v[2]
        sp = '> ' + v[3]
        sk = '< -' + v[2]
        bp = '< -' + v[3]
    elif strategy_type == '3':
        bk = '< -' + v[2]
        sp = '> -' + v[3]
        sk = '> ' + v[2]
        bp = '< ' + v[3]
    elif strategy_type == '4':
        bk = '< -' + v[2]
        sp = '< -' + v[3]
        sk = '> ' + v[2]
        bp = '> ' + v[3]

    stop_profit = v[4]
    stop_loss= v[5]
    test_time = summary['start_date'] + '/' + summary['end_date']
    total_returns = str(summary['total_returns'])
    annualized_returns = str(summary['annualized_returns'])
    max_drawdown = str(summary['max_drawdown'])

    dt_start = datetime.datetime.strptime(summary['start_date'], '%Y-%m-%d')
    dt_end = datetime.datetime.strptime(summary['end_date'], '%Y-%m-%d')
    days = (dt_end - dt_start).days
    trades_per_day = float(len(trades)) / days
    if trades_per_day < 0.05:
        score = '-1'
    else:
        score = str(round(summary['total_returns'] / summary['max_drawdown'], 4)) if summary['max_drawdown'] > 0 else '-1'

    sharpe = str(summary['sharpe'])
    trades_cnt = str(int(len(trades) / 2))
    res_line = ','.join([contract_name, test_time, bk, sp, sk, bp, stop_profit, stop_loss, score, annualized_returns, total_returns, max_drawdown, sharpe, trades_cnt])
    if output_file:
        output_file.write('%s\n' % res_line)
    else:
        print(res_line)

if output_file:
    output_file.close()
