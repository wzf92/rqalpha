from rqalpha.apis import *
from rqalpha.utils.logger import user_system_log, user_log
from logbook import FileHandler

STRATEGY_NAME = 'flow_through'


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
        logger.info("close stop")
        order_to(context.contract, 0)


def do_close(context, bar_dict):
    if bar_dict[context.contract].force_close:
        logger.info("close force")
        order_to(context.contract, 0)
        return
    if check_holding_long(context) and check_through(context, bar_dict, context.close_long_threshold):
        logger.info("close long")
        order_to(context.contract, 0)
        context.state = "NONE"
    elif check_holding_short(context) and check_through(context, bar_dict, context.close_short_threshold):
        logger.info("close short")
        order_to(context.contract, 0)
        context.state = "NONE"

def get_max_quantity(context, bar_dict):
    case = context.future_account.cash
    price = bar_dict[context.contract].close
    return int(case / price / 100)

def do_open(context, bar_dict):
    if bar_dict[context.contract].force_not_open:
        return
    if not check_holding_long(context) and not check_holding_short(context):
        if check_through(context, bar_dict, context.open_long_threshold):
            quantity = get_max_quantity(context, bar_dict)
            logger.info("open long %d" % quantity)
            order_to(context.contract, quantity)
            context.state = "HOLDING_LONG"
        elif check_through(context, bar_dict, context.open_short_threshold):
            quantity = get_max_quantity(context, bar_dict)
            logger.info("open short %d" % quantity)
            order_to(context.contract, -quantity)
            context.state = "HOLDING_SHORT"


def init_config(context):
    if "strategy" not in context.config.keys():
        assert False, "strategy null"
    if STRATEGY_NAME not in context.config.strategy.keys():
        assert False, "%s null" % STRATEGY_NAME
    cfg = context.config.strategy.flow_through
    context.contract = cfg.contract
    context.open_long_threshold = cfg.open_long_threshold
    context.close_long_threshold = cfg.close_long_threshold
    context.open_short_threshold = cfg.open_short_threshold
    context.close_short_threshold = cfg.close_short_threshold


def init(context):
    init_config(context)
    subscribe([context.contract])
    context.last_flow = np.nan
    context.state = "NONE"
    context.cnt = 0


def before_trading(context):
    pass


def handle_bar(context, bar_dict):
    if np.isnan(bar_dict[context.contract].flow_ratio):
        context.cnt += 1
        return
    if np.isnan(context.last_flow):
        context.last_flow = bar_dict[context.contract].flow_ratio
        return
    do_close(context, bar_dict)
    do_stop_profit_loss(context, bar_dict)
    do_open(context, bar_dict)
    context.last_flow = bar_dict[context.contract].flow_ratio


