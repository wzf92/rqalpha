# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。


from ..utils import assert_order

__config__ = {
    "base": {
        "start_date": "2016-03-07",
        "end_date": "2016-03-08",
        "frequency": "1d",
        "accounts": {
            "stock": 100000000
        }
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True,
        },
    },
}


def test_order_shares():
    __config__ = {
        "base": {
            "start_date": "2016-06-14",
            "end_date": "2016-06-19",
        },
    }

    # FIXME: supposed to check portfolio
    def init(context):
        context.counter = 0
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):

        context.counter += 1

        if context.counter == 1:
            order_price = bar_dict[context.s1].limit_up
            o = order_shares(context.s1, 1910, order_price)
            assert_order(o, order_book_id=context.s1, side=SIDE.BUY, quantity=1900, price=order_price)
        elif context.counter == 3:
            assert context.portfolio.positions[context.s1].quantity == 2280
            o = order_shares(context.s1, -1010, bar_dict[context.s1].limit_down)
            assert_order(o, side=SIDE.SELL, quantity=1010, status=ORDER_STATUS.FILLED)
        elif context.counter == 4:
            assert context.portfolio.positions[context.s1].quantity == 1270
            o = order_shares(context.s1, -1270, bar_dict[context.s1].limit_down)
            assert_order(o, quantity=1270, status=ORDER_STATUS.FILLED)
            assert context.portfolio.positions[context.s1].quantity == 0

    return locals()


def test_order_lots():
    def init(context):
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):
        order_price = bar_dict[context.s1].limit_up
        o = order_lots(context.s1, 1, order_price)
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, quantity=100, price=order_price)
    return locals()


def test_order_value():
    def init(context):
        context.s1 = "000001.XSHE"
        context.amount = 100

    def handle_bar(context, bar_dict):
        order_price = bar_dict[context.s1].limit_up
        # 5 块最小手续费
        o = order_value(context.s1, context.amount * order_price + 5, order_price)
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, quantity=context.amount, price=order_price)
    return locals()


def test_order_percent():
    def init(context):
        context.s1 = "000001.XSHE"

    def handle_bar(context, bar_dict):
        o = order_percent(context.s1, 0.0001, bar_dict[context.s1].limit_up)
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, price=bar_dict[context.s1].limit_up)
    return locals()


def test_order_target_value():
    def init(context):
        context.order_count = 0
        context.s1 = "000001.XSHE"
        context.amount = 10000

    def handle_bar(context, bar_dict):
        o = order_target_percent(context.s1, 0.02, style=LimitOrder(bar_dict[context.s1].limit_up))
        assert_order(o, side=SIDE.BUY, order_book_id=context.s1, price=bar_dict[context.s1].limit_up)
    return locals()


def test_auto_switch_order_value():
    __config__ = {
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-07",
            "accounts": {
                "stock": 2000
            }
        },
        "mod": {
            "sys_accounts": {
                "auto_switch_order_value": True
            },
        }
    }

    def handle_bar(context, _):
        order_shares("000001.XSHE", 200)
        assert context.portfolio.positions["000001.XSHE"].quantity == 100
    return locals()


def test_order_target_portfolio():
    __config__ = {
        "base": {
            "accounts": {
                "stock": 1000000
            }
        },
    }

    target_portfolio = {
        "000001.XSHE": 0.1,
        "000004.XSHE": 0.3,
        "000005.XSHE": 0.2
    }

    def handle_bar(context, handle_bar):
        order_target_portfolio(target_portfolio)
        total_value = context.portfolio.total_value
        for o in target_portfolio.keys():
            p = get_position(o)
            assert 0 < target_portfolio[o] - p.market_value / total_value < 0.05

    return locals()