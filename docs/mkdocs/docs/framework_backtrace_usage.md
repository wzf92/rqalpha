# 回测框架的使用
## 登陆jupyter
用浏览器打开地址: http://121.40.85.7:8878  
密码: s\*\*\*k.j\*\*\*\*\*r

## 打开notebook
路径: **playground/examples**  
目前这个路径下有两个notebook：

1. quick_start.ipynb: 对应的是米筐官方提供的示例策略
2. strategy_flow.ipynb: 流量阈值突破策略

## 建立自己的notebook目录
为了防止多人同时登陆机器环境调试，同时改动notebook环境，建议可在playground目录下建立个人目录。然后在个人目录下再创建notebook，避免notebook互相混用改动。
操作方法：

1. 进入到playground目录后，点右边的New，选择Folder；
2. 这时会多出一个目录，名称是Untitled Folder。勾选上这个目录，上面会弹出一个Rename选项，点Rename，输入名称，例如wangzf；
3. 进入个人目录，如playground/wangzf，再点New->Python3，这样就创建了一个空的notebook，然后可以将examples下的notebook内容复制进来。或者通过Duplicate再Move的方式，将examples的notebook拷贝到个人目录下。

## 运行官方的示例程序
notebook代码如下：
```python
from rqalpha import run_file

config = {
  "base": {
    "start_date": "2016-06-01",
    "end_date": "2016-12-01",
    "frequency": "1d",
    "benchmark": "000300.XSHG",
    "accounts": {
        "stock": 100000
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

strategy_file_path = "/root/projects/rqalpha/rqalpha/examples/buy_and_hold.py"

res = run_file(strategy_file_path, config)
```
将这块代码拷贝到notebook中，点击运行即可看到结果。  
其中：  

- config是参数配置，config里的base是框架基础配置，包括回测时间、回测频率、账户初始资金等；config里的mod是模块配置，不同模块会有各自的一些配置。后面
- strategy_file_path是策略路径，buy_and_hold.py这个是官方提供的示例策略，策略很简单，就是在回测开始时买入平安股票，然后一直持仓到回测结束。策略源码：
```python
from rqalpha.apis import *

# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    logger.info("init")
    context.s1 = "000001.XSHE"
    update_universe(context.s1)
    # 是否已发送了order
    context.fired = False

def before_trading(context):
    pass

# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑

    # bar_dict[order_book_id] 可以拿到某个证券的bar信息
    # context.portfolio 可以拿到现在的投资组合状态信息

    # 使用order_shares(id_or_ins, amount)方法进行落单

    # TODO: 开始编写你的算法吧！
    if not context.fired:
        # order_percent并且传入1代表买入该股票并且使其占有投资组合的100%
        order_percent(context.s1, 1)
        context.fired = True
```

## 回测报告
任何策略，回测运行完都会有以下几个报告。

### 汇总图
当配置中的sys_analyser模块开启了plot功能，就会画这张汇总图
![notebook_quick_start_1.png](http://121.40.85.7/notebook_quick_start_1.png)

### 汇总日志
在当前目录的report子目录下，有汇总日志**summary.csv**，内容其实和汇总图是一样的：  
![notebook_quick_start_2.png](http://121.40.85.7/notebook_quick_start_2.png)

### 交易日志
report/trades.csv  
![notebook_quick_start_4.png](http://121.40.85.7/notebook_quick_start_4.png)

### 每日账户资金日志
report/stock_account.csv  
![notebook_quick_start_3.png](http://121.40.85.7/notebook_quick_start_3.png)

### 每日仓位日志
report/stock_positions.csv  
![notebook_quick_start_5.png](http://121.40.85.7/notebook_quick_start_5.png)

### 投资组合？
report/portfolio.csv  
![notebook_quick_start_6.png](http://121.40.85.7/notebook_quick_start_6.png)



