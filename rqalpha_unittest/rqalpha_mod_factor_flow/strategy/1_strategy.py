from rqalpha.apis import *


def init(context):
    logger.info("init")
    context.s1 = "000001.XSHE"
    update_universe(context.s1)
    update_universe("I88")


def before_trading(context):
    pass


def handle_bar(context, bar_dict):
    pass
