import os
import sys
import glob
import pymongo
import pandas as pd

# 这个路径要和上面的"output_file"对应
#for name in glob.glob("/root/projects/rqalpha/results/*.pkl"):

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
    annualized_returns = str(summary['annualized_returns'])
    max_drawdown = str(summary['max_drawdown'])
    score = str(round(summary['total_returns'] / summary['max_drawdown'], 4))
    sharpe = str(summary['sharpe'])
    trades_cnt = str(int(len(trades) / 2))
    print(','.join([contract_name, test_time, score, bk, sp, sk, bp, annualized_returns, max_drawdown, sharpe, stop_profit, stop_loss, trades_cnt]))
