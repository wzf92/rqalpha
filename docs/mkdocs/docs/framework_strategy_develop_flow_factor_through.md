# 策略开发示例(流量突破策略)
## 1.创建策略文件
在`rqalpha/examples/`新建一个`strategy_flow_through_demo.py`文件(其实位置、命名都没有强制限制)

## 2.编写策略
策略模版：
```python
from rqalpha.apis import *

def init(context):
    # 初始化，必须订阅至少一个交易品种的数据，不然框架会报错
    # context.s1 = 'I88'
    # subscribe([context.s1])


def handle_bar(context, bar_dict):
    # 开平仓的判断逻辑、仓位调整
    pass
```

流量突破策略：
```python
# 导入框架借口，这行是固定需要的
from rqalpha.apis import *

# 策略初始化函数，必须要有
def init(context):
    # 初始化回测品种、流量突破阈值。值放在context结构体里，context是上下文的意思,
    # 起到的作用类似于全局变量传递。可以在具体策略执行函数(handler_bar)时取到需要的值
    context.contract = "I88"
    context.open_long_threshold = "> 0.1"
    context.close_long_threshold = "< 0.1"
    context.open_short_threshold = "< -0.1"
    context.close_short_threshold = "> -0.1"
    context.last_flow = np.nan
    # 订阅回测品种的数据，也就是告诉回测框架，你这次回测需要哪些品种的数据。必须要有。
    subscribe([context.contract])


# 具体的策略执行函数，这个函数会处理EVENT.BAR事件
def handle_bar(context, bar_dict):
    # 如果流量因子还不可用(即处于初始化阶段)，不做任何事直接返回
    if np.isnan(bar_dict[context.contract].flow_ratio):
        return
    # 如果上一次的流量因子未初始化，将其初始化，然后返回
    if np.isnan(context.last_flow):
        context.last_flow = bar_dict[context.contract].flow_ratio
        return
    # 平仓判断和执行
    do_close(context, bar_dict)
    # 开仓判断和执行
    do_open(context, bar_dict)
    # 更新上一次的流量为当前流量
    context.last_flow = bar_dict[context.contract].flow_ratio

# 平仓判断和执行
def do_close(context, bar_dict):
    # 如果持多，并且流量因子的变化穿过了close_long_threshold阈值
    if check_holding_long(context) and check_through(context, bar_dict, context.close_long_threshold):
        # 平仓
        order_to(context.contract, 0)
    # 如果持空，并且流量因子的变化穿过了close_short_threshold阈值
    elif check_holding_short(context) and check_through(context, bar_dict, context.close_short_threshold):
        # 平仓
        order_to(context.contract, 0)


# 开仓判断和执行
def do_open(context, bar_dict):
    # 如果没有持仓
    if not check_holding_long(context) and not check_holding_short(context):
        # 如果流量因子的变化穿过了open_long_threshold阈值
        if check_through(context, bar_dict, context.open_long_threshold):
            # 将仓位调整到1手(即持多)
            order_to(context.contract, 1)
        # 如果流量因子的变化穿过了open_short_threshold阈值
        elif check_through(context, bar_dict, context.open_short_threshold):
            # 将仓位调整到-1手(即持空)
            order_to(context.contract, -1)

# 判断是否持多
def check_holding_long(context):
    return get_position(context.contract, POSITION_DIRECTION.LONG).quantity != 0


# 判断是否持空
def check_holding_short(context):
    return get_position(context.contract, POSITION_DIRECTION.SHORT).quantity != 0


# 判断流量是否穿越阈值
def check_through(context, bar_dict, condition):
    direction = condition[0]
    threshold = float(condition.split(" ")[1])
    assert direction in [">", "<"]
    if direction == ">":
        if context.last_flow <= threshold < bar_dict[context.contract].flow_ratio:
            return True
        else:
            return False
    else:
        if context.last_flow >= threshold > bar_dict[context.contract].flow_ratio:
            return True
        else:
            return False
```

## 3.在jupyter里运行策略
1. 打开jupyter (http://121.40.85.7:8878)
2. 进入目录`playground/个人目录` (参考[回测框架的使用](http://121.40.85.7:8000/framework_backtrace_usage/))
3. 新建一个notebook
4. 调用策略的代码如下：
```python
from rqalpha import run_file

config = {
  "base": {
    "start_date": "2020-01-01",
    "end_date": "2020-12-01",
    "frequency": "1m",
    "accounts": {
        "future": 100000
    }
  },
  "mod": {
    "sys_analyser": {
      "enabled": True,
      "report_save_path": "report",
      "plot": True
    }
  }
}

strategy_file_path = "/root/projects/rqalpha/rqalpha/examples/strategy_flow_through_demo.py"

res = run_file(strategy_file_path, config)
```
运行后，可以看到回测结果：
![framework_strategy_develop_flow_through_1.png](http://121.40.85.7/framework_strategy_develop_flow_through_1.png)
详情报告在`playground/个人目录/report`下。

