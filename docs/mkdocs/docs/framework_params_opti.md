# 参数遍历调优
## 多线程并发执行策略
举个例子：假如想遍历I88这个品种，流量阈值为0.1、0.2、0.3、0.4这四种情况的回测结果

```python
# 这两个模块用于多线程并发
import concurrent.futures
import multiprocessing

from rqalpha import run


# 第一步：先构造出一个tasks，内容是config的列表，每一个config对应一组回测参数
tasks = []
for iterator in range(1, 5):
    # threshold: 0.1, 0.2, 0.3, 0.4
    threshold = float(iterator) / 10
    config = {
      "base": {
        # 策略的路径，必须要有
        "strategy_file": "/root/projects/rqalpha/rqalpha/examples/strategy_flow.py",
        "start_date": "2020-01-01",
        "end_date": "2020-12-01",
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
          "enabled": True,
          # 回测结果的保存路径，必须要有
          "output_file": "/root/projects/rqalpha/results/I88-{threshold}.pkl".format(
                          threshold = threshold,
          )
        }
      },
      "strategy": {
          "flow_through":
          {
              "contract": "I88",
              # 遍历参数填充
              "open_long_threshold": "> %f" % threshold,
              "close_long_threshold": "< %f" % threshold,
              "open_short_threshold": "< -%f" % threshold,
              "close_short_threshold": "> -%f" %threshold,
          }
      }
    }
    tasks.append(config)

# 第二步：多线程并发执行回测任务
if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        for task in tasks:
            executor.submit(run, task)
```
运行结束后，会在`/root/projects/rqalpha/results`目录下生成I88-0.1.pkl、I88-0.2.pkl、I88-0.3.pkl、I88-0.4.pkl四个文件

## 遍历结果分析
```python
import os
import glob
import pandas as pd

results = []

# 这个路径要和上面的"output_file"对应
for name in glob.glob("/root/projects/rqalpha/results/*.pkl"):
    result_dict = pd.read_pickle(name)
    # summary即回测报告中的summary.csv中的内容
    summary = result_dict["summary"]
    # 假如我们只关注夏普率和年化收益率
    results.append({
        "name": os.path.basename(name),
        "annualized_returns": summary["annualized_returns"],
        "sharpe": summary["sharpe"],
    })

results_df = pd.DataFrame(results)

# 按夏普率降序排列
print("-" * 50)
print("Sort by sharpe")
print(results_df.sort_values("sharpe", ascending=False))

# 按年化收益率降序排列
print("-" * 50)
print("Sort by annualized_returns")
print(results_df.sort_values("annualized_returns", ascending=False))
```
分析结果：
![framework_params_opti_1.png](http://121.40.85.7/framework_params_opti_1.png)
