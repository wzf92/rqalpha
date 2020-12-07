# 流量突破
## 整体思路
根据流量因子，当流量突破指定的阈值时，执行开仓/平仓操作

## 模块依赖
- [流量因子](http://121.40.85.7:8000/mod_flow_factor/)

## 策略参数
策略名称: flow_through

名称|值类型|默认值|描述
:-|:-|:-|:-
open_long_threshold|string|"> 0.5"|指定触发open_long的流量突破方向+流量阈值，">"表示向上突破，"<"表示向下突破，中间必须要有空格
close_long_threshold|string|"< 0.5"|指定触发closse_long的流量突破方向+流量阈值，">"表示向上突破，"<"表示向下突破，中间必须要有空格
open_short_threshold|string|"< -0.5"|指定触发open_short的流量突破方向+流量阈值，">"表示向上突破，"<"表示向下突破，中间必须要有空格
close_short_threshold|string|"> -0.5"|指定触发closse_short的流量突破方向+流量阈值，">"表示向上突破，"<"表示向下突破，中间必须要有空格
