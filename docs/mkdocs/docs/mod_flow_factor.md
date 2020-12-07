# 流量因子
## 含义
描述交易品种的资金流向。大于零时，表示短期内有资金流入；小于零时有资金流出。

## 接口
###输入参数
- bar_dict[symbol].close
- bar_dict[symbol].volume

###输出参数
- bar_dict[symbol].last_flow_ratio (type: float)
- bar_dict[symbol].flow_ratio (type: float)

###执行阶段
- PRE_BAR

## 计算逻辑
### 步骤
1. 输入流量 = 最近1个统计周期的close_price * sum(最近n个统计周期的volume, n = [1, 240])
2. 输出流量 = sum(最近第n个统计周期的close_price * 最近第n个统计周期的volume, n = [1, 240])
3. 流量大小 = 输入流量 - 输出流量
4. 归一化后的流量 = 流量大小 / max(最近m个周期的流量大小, m = 2000) * 100%

### 伪代码示例
```
# 输入流量
size_total = size_1 + size_2 + size_3 + ... + size_240
in_flow = close_price_240 * size_total

# 输出流量
out_flow = close_price_1*size_1 + close_price_2*size_2 + ... + close_price_240*size_240

# 流量大小
E240_value = in_flow - out_flow

# 流量归一化
E240_ratio = E240_value / max(abs(最近的2000个E240_value)) * 100%
```

## 模块参数
名称|值类型|默认值|描述
:-|:-|:-|:-
slice|int|240|计算一次流量因子的统计周期数
size|int|2000|归一化取的最近多少个流量值
log_dir|string|None|日志路径
