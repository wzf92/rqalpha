from rqalpha.apis import *



def check_holding_long(context):
    return get_position(context.contract, POSITION_DIRECTION.LONG).quantity != 0


def check_holding_short(context):
    return get_position(context.contract, POSITION_DIRECTION.SHORT).quantity != 0


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

def do_stop_profit_loss(context, bar_dict):
    if not check_holding_long(context) and not check_holding_short(context):
        return
    if bar_dict[context.contract].stop_profit or bar_dict[context.contract].stop_loss:
        order_to(context.contract, 0)


def do_close(context, bar_dict):
    if bar_dict[context.contract].force_close:
        order_to(context.contract, 0)
        return
    if check_holding_long(context) and check_through(context, bar_dict, context.close_long_threshold):
        order_to(context.contract, 0)
    elif check_holding_short(context) and check_through(context, bar_dict, context.close_short_threshold):
        order_to(context.contract, 0)


def do_open(context, bar_dict):
    if bar_dict[context.contract].force_not_open:
        return
    if not check_holding_long(context) and not check_holding_short(context):
        if check_through(context, bar_dict, context.open_long_threshold):
            order_to(context.contract, 1)
        elif check_through(context, bar_dict, context.open_short_threshold):
            order_to(context.contract, -1)


def init(context):
    context.contract = "I88"
    context.open_long_threshold = "> 0.1"
    context.close_long_threshold = "< 0.1"
    context.open_short_threshold = "< -0.1"
    context.close_short_threshold = "> -0.1"
    subscribe([context.contract])
    context.last_flow = np.nan


def handle_bar(context, bar_dict):
    if np.isnan(bar_dict[context.contract].flow_ratio):
        return
    if np.isnan(context.last_flow):
        context.last_flow = bar_dict[context.contract].flow_ratio
        return
    do_close(context, bar_dict)
    do_stop_profit_loss(context, bar_dict)
    do_open(context, bar_dict)
    context.last_flow = bar_dict[context.contract].flow_ratio
