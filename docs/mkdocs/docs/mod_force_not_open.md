# 强制不开仓
## 含义
在特定时间段内，给出强制不开仓的标志位(不会实际去限制开仓操作，交由策略模块处理)。

## 接口
###输入参数
- event.calendar_dt

###输出参数
- bar_dict[symbol].force_not_open (type: bool)

###执行阶段
- PRE_BAR

## 计算逻辑
### 步骤
  1. 判断当前时间是否在配置的时间内，不是的话返回
  2. 设置强制不开仓的标志位

### 伪代码
```python
# force_not_open_time_list = ['14:30-15:00', '22:30-23:00']
bar_dict[contract].force_not_open = False
for force_not_open_time in force_not_open_time_list:
  if cur_time in force_not_open_time:
      bar_dict[contract].force_not_open = True
```

## 模块参数
名称|值类型|默认值|描述
:-|:-|:-|:-
force_not_open_time|list|["14:30-15:00", "22:30-23:00"]|强制不开仓的时间段
log_dir|string|None|日志路径

