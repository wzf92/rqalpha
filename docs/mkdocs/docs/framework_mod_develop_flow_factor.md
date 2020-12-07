# 模块开发示例(流量因子)
## 1. 创建模块目录
在项目目录`rqalpha/mod`下，新建一个目录，目录名称为`rqalpha_mod_factor_flow`。其中`rqalpha_mod_`是固定前缀，不要写其他。`factor_flow`是具体模块名称，可自由命名。
## 2. 创建模块基本框架代码
在模块目录`rqalpha/mod/rqalpha_mod_factor_flow`下，新建两个文件，`__init__.py`和`mod.py`。两个都是固定这个名称。
## 3. 编写__init__.py
内容如下：
```python
__config__ = { 
    "slice": 240,
    "size": 2000,
}

def load_mod():
      from .mod import CalcFlowFactor
          return CalcFlowFactor()
```
1. `__config__`是模块参数字典，定义哪些参数支持配置。对于流量因子来说，最主要的两个计算参数：`slice`表示一个统计周期是多少分钟，默认值240分钟; `size`表示因子归一化时取的是最近几个流量因子的最大值，默认值2000个。
2. `load_mod`函数固定，里面的`CalcFlowFactor`可自由命名，意思是计算流量因子的类。
## 4. 编写mod.py
`mod.py`的编写模板如下：
```python
from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT

class ModName(AbstractMod):
    def __init__(self):
        pass

    def start_up(self, env, mod_config):
        pass

    def tear_down(self, success, exception=None):
        pass
```

对于流量因子计算模块，内容如下：
```python
# 这两个模块是固定需要导入的
from rqalpha.interface import AbstractMod
from rqalpha.events import EVENT

# 这几个模块是计算需要
from collections import defaultdict
import numpy as np
import os

# 类名自由取，必须继承于AbstractMod
class CalcFlowFactor(AbstractMod):
    # 构造函数。初始化需要使用的成员变量。
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

    # start_up函数必须有。这个函数会在框架初始化时调用，函数主要要做两件事：读取模块配置和设置监听的事件类型
    def start_up(self, env, mod_config):
        # 读取模块配置。例如mod_config.slice对应的是__init__.py里的__config__的"slice"属性。
        self._kline_bar_cnt = mod_config.slice
        self._save_flow_value_cnt = mod_config.size
        if "log_dir" in mod_config.keys():
            self._log_dir = mod_config.log_dir

        # 设置监听的事件类型。这行代码直接翻译出来的意思就是：当回测框架产生事件EVENT.PRE_BAR时，就调用self._update_flow这个函数来处理。
        # 因为回测策略注册的事件类型是EVENT.BAR，对于因子计算，可以设置注册类型为EVENT.PRE_BAR(PRE表示之前，即框架会先产生EVENT.PRE_BAR，再产生EVENT.BAR)，这样就能保证执行到策略，因子已经计算出来。
        env.event_bus.add_listener(EVENT.PRE_BAR, self._update_flow)

    # tear_down函数必须有。这个函数会在程序结束时调用。负责做些收尾的事，比如关闭日志文件啥的。
    def tear_down(self, success, exception=None):
        for f in self._log_file.values():
            if f:
                f.close()

    # 这个函数对应start_up里的env.event_bus.add_listener的第二个参数，是计算流量因子的入口函数
    def _update_flow(self, event):
        # contract_list是包含当前策略所有交易品种的列表，例如如果是做I88流量突破策略的话，contract_list = ["I88"]
        contract_list = list(event.bar_dict.keys())
        # 遍历列表中的每一个品种
        for contract in contract_list:
            # 初始化流量因子的值为nan(Not A Number)
            event.bar_dict[contract].flow_ratio = np.nan
            # 如果当前的bar数据不可用的话(比如kline某一分钟的数据缺失了)，直接跳过计算
            if event.bar_dict[contract].isnan:
                continue
            # 尝试计算流量因子，返回True时表示计算成功
            if self._update_flow_one_contract(contract, event.bar_dict[contract]):
                # 更新流量因子，注意，存储位置是: bar_dict[contract].flow_ratio，这个会在策略里用到
                event.bar_dict[contract].flow_ratio = self._cur_flow_ratio[contract]



    # 这个函数被_update_flow调用，作用是计算一个交易品种的流量因子
    # 这部分是流量因子具体计算的过程
    def _update_flow_one_contract(self, c, bar):
        # 计算inflow
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
        # 如果inflow还不可用(也就是还未满240个统计周期，算不出来值)，返回False
        if not self._kline_bar_enable[c]:
            return False
        # 计算outflow
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
        # 如果流量因子还未算满2000个(归一化需要的历史个数)，返回False
        if not self._save_flow_value_enable[c]:
            return False
        # 归一化
        self._cur_flow_ratio[c] = round(self._cur_flow[c] / self._max_flow[c], 6)
        # 后面是日志纪录流量因子的值
        if not self._log_dir:
            return True
        if not self._log_file[c]:
            path = os.path.join(self._log_dir, c + '_flow.csv')
            self._log_file[c] = open(path, 'w')
        msg = "%s,%s" % (str(bar.datetime), self._cur_flow_ratio[c])
        self._log_file[c].write(msg + "\n")
        return True

    # 更新归一化用的分母
    def _update_max_flow(self, c, new_flow, del_flow):
        assert del_flow <= self._max_flow[c]
        if del_flow == self._max_flow[c]:
            self._max_flow[c] = max(self._save_flow_value_list[c])
            return
        if new_flow > self._max_flow[c]:
            self._max_flow[c] = new_flow
        return
```
## 5. 将模块加入到rqalpha框架
1) 修改`rqalpha/mod_config.yml`文件，在末尾加上：
```yml
  flow_factor:
    enabled: true
```
注意：

1. 格式缩进要对齐；
2. `factor_flow`这个名字对应的是第1步当中的`rqalpha_mod_`之后的名字；
3. `enabled: true`表示打开该模块，固定的。

2) 修改`rqalpha/mod/__init__.py`文件，在最后的`SYSTEM_MOD_LIST`加上模块名：
```python
SYSTEM_MOD_LIST = [
  ...
  "factor_flow",
]
```

## 6. 更新rqalpha(加上新的模块)
终端登陆服务器，然后执行:
```bash
$ cd ~/projects/rqalpha
$ python setup.py install
```
成功的话，可以看到命令行输出：
```bash
...... (省略)
Using /root/anaconda3/lib/python3.7/site-packages
Finished processing dependencies for rqalpha==4.2.2+18.g67b7e823.dirty
```

## 7. 调试(在策略里获取流量因子的值)
在完成1-6步后，计算流量因子的模块已经完成了。这一步是验证能在策略里取到因子的值。具体步骤：

1. 打开jupyter (http://121.40.85.7:8878)
2. 进入目录`playground/个人目录` (参考[回测框架的使用](http://121.40.85.7:8000/framework_backtrace_usage/))
3. 新建一个notebook
4. 测试代码如下：
```python
# run_func_demo
from rqalpha.api import *
from rqalpha import run_func
import numpy as np


def init(context):
    context.s1 = "I88"
    update_universe(context.s1)


def handle_bar(context, bar_dict):
    if np.isnan(bar_dict[context.s1].flow_ratio):
        logger.info("flow_ratio invalid")
        return
    logger.info("flow_ratio = %f" % bar_dict[context.s1].flow_ratio)

    
config = {
  "base": {
    "start_date": "2016-06-01",
    "end_date": "2016-12-01",
    "frequency": "1m",
    "accounts": {
        "future": 100000
    }
  },
  "extra": {
    "log_level": "info",
  }
}

run_func(init=init, handle_bar=handle_bar, config=config)
```

运行后，可看到结果，刚开始输出的都是"flow_ratio invalid"，后面输出具体的流量因子值
![framework_mod_develop_flow_factor_1.png](http://121.40.85.7/framework_mod_develop_flow_factor_1.png)

