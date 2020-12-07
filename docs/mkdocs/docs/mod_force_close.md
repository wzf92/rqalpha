# 强制平仓
## 含义
在特定时间段内，若有持仓，给出强制平仓的标志位(不实际去做平仓操作，交由策略模块处理)。

## 接口
###输入参数
- event.calendar_dt
- long_positions, short_positions

###输出参数
- bar_dict[symbol].force_close (type: bool)

###执行阶段
- PRE_BAR

## 计算逻辑
### 步骤
  1. 判断当前时间是否在配置的时间内，不是的话返回
  2. 判断当前交易品种是否有持仓, 不是的话返回
  3. 设置强制平仓的标志位

### 伪代码
```python
# force_close_time_list = ['14:55-15:00', '22:55-23:00']
bar_dict[contract].force_close = False
for force_close_time in force_close_time_list:
  if cur_time in force_close_time and long_positions.quantity + short_positions.quantity > 0 :
      bar_dict[contract].force_close = True
```

## 模块参数
名称|值类型|默认值|描述
:-|:-|:-|:-
force_close_time|list|["14:55-15:00", "22:55-23:00"]|强制平仓的时间段
log_dir|string|None|日志路径

