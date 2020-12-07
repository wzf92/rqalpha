# 止盈止损
## 含义
当某个品种的持仓收益率大于某个上限值，或者小于某个下限值时，给出标志位信号(不实际做平仓操作，交由策略自己执行)。 

## 接口
###输入参数
- long_positions.pnl_ratio
- short_positions.pnl_ratio

###输出参数
- bar_dict[symbol].stop_profit (type: bool)
- bar_dict[symbol].stop_loss (type: bool)

###执行阶段
- PRE_BAR

## 计算逻辑
### 步骤
  1. 判断当前持仓收益率是否超出限制
  2. 设置止盈止损平仓的标志位

### 伪代码
```python
# stop_profit = 0.03, stop_loss = 0.03
bar_dict[contract].stop_profit = False
bar_dict[contract].stop_loss = False
if long_positions.pnl_ratio >= stop_profit or short_positions.pnl_ratio >= stop_profit:
    bar_dict[contract].stop_profit = True
elif long_positions.pnl_ratio <= -stop_loss or short_positions.pnl_ratio <= -stop_loss:
    bar_dict[contract].stop_loss = True
```

## 模块参数
名称|值类型|默认值|描述
:-|:-|:-|:-
stop_profit|float|0.03|止盈阈值
stop_loss|float|0.03|止损阈值
