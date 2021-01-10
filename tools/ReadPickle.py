import os
import sys
import glob
import pymongo
import pandas as pd

# 这个路径要和上面的"output_file"对应
#for name in glob.glob("/root/projects/rqalpha/results/*.pkl"):
print(glob.glob(sys.argv[1]))
for name in glob.glob(sys.argv[1]):
    result_dict = pd.read_pickle(name)
    # summary即回测报告中的summary.csv中的内容
    summary = result_dict["summary"]
    print(summary)
