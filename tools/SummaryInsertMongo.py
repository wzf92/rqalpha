import os
import sys
import glob
import pymongo
import pandas as pd

host = "121.40.85.7"
port = 9999
server_addr = "mongodb://%s:%d/" % (host, port)
client = pymongo.MongoClient(server_addr)

# 这个路径要和上面的"output_file"对应
#for name in glob.glob("/root/projects/rqalpha/results/*.pkl"):
print(glob.glob(sys.argv[1]))
for name in glob.glob(sys.argv[1]):
    print("insert %s" % name)
    basename = os.path.basename(name)
    v = basename.replace(".pkl", "").split("-")
    contract = v[0]
    strategy_type = v[1]
    threshold_1 = v[2]
    threshold_2 = v[3]
    stop_profit = v[4]
    stop_loss = v[5]
    result_dict = pd.read_pickle(name)
    # summary即回测报告中的summary.csv中的内容
    summary = result_dict["summary"]
    if strategy_type == "1":
        summary["open_long_threshold"] = "> %s" % threshold_1
        summary["close_long_threshold"] = "< %s" % threshold_1
        summary["open_short_threshold"] = "< -%s" % threshold_2
        summary["close_short_threshold"] = "> -%s" % threshold_2
    elif strrategy_type == "2":
        summary["open_long_threshold"] = "> %s" % threshold_1
        summary["close_long_threshold"] = "> %s" % threshold_1
        summary["open_short_threshold"] = "< -%s" % threshold_2
        summary["close_short_threshold"] = "< -%s" % threshold_2
    elif strrategy_type == "3":
        summary["open_long_threshold"] = "< -%s" % threshold_1
        summary["close_long_threshold"] = "> -%s" % threshold_1
        summary["open_short_threshold"] = "> %s" % threshold_2
        summary["close_short_threshold"] = "< %s" % threshold_2
    elif strrategy_type == "4":
        summary["open_long_threshold"] = "< -%s" % threshold_1
        summary["close_long_threshold"] = "< -%s" % threshold_1
        summary["open_short_threshold"] = "> %s" % threshold_2
        summary["close_short_threshold"] = "> %s" % threshold_2
    client["backtrace_report_flow_through"][contract].insert_one(summary)
