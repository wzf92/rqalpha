# 这两个模块用于多线程并发
import concurrent.futures
import multiprocessing

from rqalpha import run


types = {
        "1": {"ol": ">", "cl": "<", "os": "<", "cs":">"},        
        "2": {"ol": ">", "cl": ">", "os": "<", "cs":"<"},        
        "3": {"ol": "<", "cl": ">", "os": ">", "cs":"<"},        
        "4": {"ol": "<", "cl": "<", "os": ">", "cs":">"},        
}

tasks = []
for k,v in types.items():
    for iterator1 in range(1, 10):
        for iterator2 in range(1, 10):
            it1 = round(float(iterator1) / 10, 1)
            it2 = round(float(iterator2) / 10, 1)
            config = {
              "base": {
                # 策略的路径，必须要有
                "strategy_file": "/root/projects/rqalpha/rqalpha/examples/strategy_flow.py",
                "start_date": "2015-01-01",
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
                  "output_file": "/root/projects/rqalpha/results/I88-{now_type}-{it1}-{it2}-0.01-0.01.pkl".format(
                                  now_type=k, it1=it1, it2=it2,
                  )
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
                  "stop_profit": 0.01,
                  "stop_loss": 0.01,
                }
              },
              "strategy": {
                  "flow_through":
                  {
                      "contract": "I88",
                      # 遍历参数填充
                      "open_long_threshold": "%s %f" % (v["ol"], it1),
                      "close_long_threshold": "%s %f" % (v["cl"], it2),
                      "open_short_threshold": "%s -%f" % (v["os"], it1),
                      "close_short_threshold": "%s -%f" % (v["cs"], it2),
                  }
              }
            }
            tasks.append(config)

# 第二步：多线程并发执行回测任务
if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        for task in tasks:
            executor.submit(run, task)
