# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np

from rqalpha.const import SIDE, POSITION_EFFECT, ORDER_STATUS, COMMISSION_TYPE, MARGIN_TYPE
from rqalpha.model.order import LimitOrder

from ..utils import make_order_book_id, make_underlying_symbol, is_future, bytes2str
from .pyctp import ApiStruct


SIDE_REVERSE = {
    ApiStruct.D_Buy: SIDE.BUY,
    ApiStruct.D_Sell: SIDE.SELL,
}


class DataDict(dict):
    def __init__(self, d=None):
        if d:
            super(DataDict, self).__init__(d)
        else:
            super(DataDict, self).__init__()

    def copy(self):
        return DataDict(super(DataDict, self).copy())

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)


class TickDict(DataDict):
    def __init__(self, data=None):
        super(TickDict, self).__init__()
        self.order_book_id = None
        self.date = None
        self.time = None
        self.open = None
        self.last = None
        self.low = None
        self.high = None
        self.prev_close = None
        self.volume = None
        self.total_turnover = None
        self.open_interest = None
        self.prev_settlement = None

        self.b1 = None
        self.b2 = None
        self.b3 = None
        self.b4 = None
        self.b5 = None

        self.b1_v = None
        self.b2_v = None
        self.b3_v = None
        self.b4_v = None
        self.b5_v = None

        self.a1 = None
        self.a2 = None
        self.a3 = None
        self.a4 = None
        self.a5 = None

        self.a1_v = None
        self.a2_v = None
        self.a3_v = None
        self.a4_v = None
        self.a5_v = None

        self.limit_down = None
        self.limit_up = None

        self.is_valid = False

        if data:
            self.update_data(data)

    def update_data(self, data):
        self.order_book_id = make_order_book_id(data.InstrumentID)
        try:
            self.date = int(data.TradingDay)
            self.time = int((bytes2str(data.UpdateTime).replace(':', ''))) * 1000 + int(data.UpdateMillisec)
            self.open = data.OpenPrice
            self.last = data.LastPrice
            self.low = data.LowestPrice
            self.high = data.HighestPrice
            self.prev_close = data.PreClosePrice
            self.volume = data.Volume
            self.total_turnover = data.Turnover
            self.open_interest = data.OpenInterest
            self.prev_settlement = data.SettlementPrice

            self.b1 = data.BidPrice1
            self.b2 = data.BidPrice2
            self.b3 = data.BidPrice3
            self.b4 = data.BidPrice4
            self.b5 = data.BidPrice5
            self.b1_v = data.BidVolume1
            self.b2_v = data.BidVolume2
            self.b3_v = data.BidVolume3
            self.b4_v = data.BidVolume4
            self.b5_v = data.BidVolume5
            self.a1 = data.AskPrice1
            self.a2 = data.AskPrice2
            self.a3 = data.AskPrice3
            self.a4 = data.AskPrice4
            self.a5 = data.AskPrice5
            self.a1_v = data.AskVolume1
            self.a2_v = data.AskVolume2
            self.a3_v = data.AskVolume3
            self.a4_v = data.AskVolume4
            self.a5_v = data.AskVolume5

            self.limit_up = data.UpperLimitPrice
            self.limit_down = data.LowerLimitPrice
            self.is_valid = True
        except ValueError:
            self.is_valid = False


# 由持仓构建的伪 tick 类，用于在拿不到行情的时候提供 last_board 。
class FakeTickDict(TickDict):
    def __init__(self, pos_dict):
        super(FakeTickDict, self).__init__()
        self.update_data(pos_dict)

    def update_data(self, data):
        self.last = data.prev_settle_price
        self.limit_up = data.prev_settle_price * 1.1
        self.limit_down = data.prev_settle_price * 0.9


class PositionDict(DataDict):
    def __init__(self, data, ins_dict=None):

        super(PositionDict, self).__init__()
        self.order_book_id = make_order_book_id(data.InstrumentID)
        self.buy_old_quantity = 0
        self.buy_quantity = 0
        self.buy_today_quantity = 0
        self.buy_transaction_cost = 0.
        self.buy_realized_pnl = 0.
        self.buy_avg_open_price = 0.
        self.sell_old_quantity = 0
        self.sell_quantity = 0
        self.sell_today_quantity = 0
        self.sell_transaction_cost = 0.
        self.sell_realized_pnl = 0.
        self.sell_avg_open_price = 0.
        self.prev_settle_price = 0.

        self.buy_open_cost = 0.
        self.sell_open_cost = 0.

        self.contract_multiplier = ins_dict.contract_multiplier if ins_dict is not None else 1

        self.is_valid = False

        self.update_data(data)

    def update_data(self, data):
        if data.PosiDirection in [ApiStruct.PD_Net, ApiStruct.PD_Long]:
            if data.YdPosition and not data.TodayPosition:
                self.buy_old_quantity = data.Position
            if data.YdPosition and data.TodayPosition:
                self.buy_old_quantity = data.Position - data.TodayPosition
            if data.TodayPosition:
                self.buy_today_quantity = data.TodayPosition

            self.buy_quantity += data.Position
            self.buy_transaction_cost += data.Commission
            self.buy_realized_pnl += data.CloseProfit

            self.buy_open_cost += data.OpenCost
            self.buy_avg_open_price = self.buy_open_cost / (self.buy_quantity * self.contract_multiplier) if self.buy_quantity > 0 else 0

        elif data.PosiDirection == ApiStruct.PD_Short:
            if data.YdPosition:
                self.sell_old_quantity = data.Position
            if data.TodayPosition:
                self.sell_today_quantity = data.TodayPosition

            self.sell_quantity += data.Position
            self.sell_transaction_cost += data.Commission
            self.sell_realized_pnl += data.CloseProfit

            self.sell_open_cost += data.OpenCost
            self.sell_avg_open_price = self.sell_open_cost / (self.sell_quantity * self.contract_multiplier) if self.sell_quantity > 0 else 0

        if data.PreSettlementPrice:
            self.prev_settle_price = data.PreSettlementPrice

        self.is_valid = True


class AccountDict(DataDict):
    def __init__(self, data):
        super(AccountDict, self).__init__()
        self.yesterday_portfolio_value = data.PreBalance


class InstrumentDict(DataDict):
    def __init__(self, data):
        super(InstrumentDict, self).__init__()
        self.order_book_id = None
        self.underlying_symbol = None
        self.exchange_id = None
        self.contract_multiplier = None
        self.long_margin_ratio = None
        self.short_margin_ratio = None
        self.margin_type = None
        self.instrument_id = None

        self.is_valid = False

        self.update_data(data)

    def update_data(self, data):
        if is_future(data.InstrumentID):
            self.order_book_id = make_order_book_id(data.InstrumentID)
            self.underlying_symbol = make_underlying_symbol(data.InstrumentID)
            self.exchange_id = data.ExchangeID
            self.contract_multiplier = data.VolumeMultiple
            self.long_margin_ratio = data.LongMarginRatio
            self.short_margin_ratio = data.ShortMarginRatio
            self.margin_type = MARGIN_TYPE.BY_MONEY
            self.instrument_id = bytes2str(data.InstrumentID)
            self.is_valid = True
        else:
            self.is_valid = False


class CommissionDict(DataDict):
    def __init__(self, data):
        super(CommissionDict, self).__init__()
        self.underlying_symbol = None
        self.close_ratio = None
        self.open_ratio = None
        self.close_today_ratio = None
        self.commission_type = None

        self.is_valid = False
        if data is not None:
            self.update_data(data)

    def update_data(self, data):
        self.underlying_symbol = make_underlying_symbol(data.InstrumentID)
        if data.OpenRatioByMoney == 0 and data.CloseRatioByMoney:
            self.open_ratio = data.OpenRatioByVolume
            self.close_ratio = data.CloseRatioByVolume
            self.close_today_ratio = data.CloseTodayRatioByVolume
            if data.OpenRatioByVolume != 0 or data.CloseRatioByVolume != 0:
                self.commission_type = COMMISSION_TYPE.BY_VOLUME
            else:
                self.commission_type = None
        else:
            self.open_ratio = data.OpenRatioByMoney
            self.close_ratio = data.CloseRatioByMoney
            self.close_today_ratio = data.CloseTodayRatioByMoney
            if data.OpenRatioByVolume == 0 and data.CloseRatioByVolume== 0:
                self.commission_type = COMMISSION_TYPE.BY_MONEY
            else:
                self.commission_type = None
        self.is_valid = True


class OrderDict(DataDict):
    def __init__(self, data, rejected=False):
        super(OrderDict, self).__init__()
        self.order_id = None
        self.order_book_id = None
        self.front_id = None
        self.session_id = None
        self.exchange_id = None

        self.quantity = None
        self.filled_quantity = None
        self.unfilled_quantity = None
        self.side = None
        self.price = None
        self.position_effect = None
        self.status = None

        self.style = None
        self.is_valid = False

        self.update_data(data, rejected)

    def update_data(self, data, rejected=False):
        if not data.InstrumentID:
            return
        try:
            self.order_id = int(data.OrderRef)
        except ValueError:
            self.order_id = np.nan

        self.order_book_id = make_order_book_id(data.InstrumentID)

        try:
            self.front_id = data.FrontID
            self.session_id = data.SessionID
        except AttributeError:
            pass

        self.quantity = data.VolumeTotalOriginal

        try:
            self.filled_quantity = data.VolumeTraded
            self.unfilled_quantity = self.quantity - self.filled_quantity
        except AttributeError:
            pass

        self.side = SIDE_REVERSE.get(data.Direction, SIDE.BUY)
        self.price = data.LimitPrice
        try:
            self.exchange_id = data.ExchangeID
        except AttributeError:
            pass

        if self.exchange_id == 'SHFE':
            if data.CombOffsetFlag == ApiStruct.OF_Open:
                self.position_effect = POSITION_EFFECT.OPEN
            elif data.CombOffsetFlag == ApiStruct.OF_CloseToday:
                self.position_effect = POSITION_EFFECT.CLOSE_TODAY
            else:
                self.position_effect = POSITION_EFFECT.CLOSE
        else:
            if data.CombOffsetFlag == ApiStruct.OF_Open:
                self.position_effect = POSITION_EFFECT.OPEN
            else:
                self.position_effect = POSITION_EFFECT.CLOSE

        if rejected:
            self.status = ORDER_STATUS.REJECTED
        else:
            try:
                if data.OrderStatus in [ApiStruct.OST_PartTradedQueueing, ApiStruct.OST_NoTradeQueueing]:
                    self.status = ORDER_STATUS.ACTIVE
                elif data.OrderStatus == ApiStruct.OST_AllTraded:
                    self.status = ORDER_STATUS.FILLED
                elif data.OrderStatus == ApiStruct.OST_Canceled:
                    self.status = ORDER_STATUS.CANCELLED
                else:
                    return
            except AttributeError:
                pass

        self.style = LimitOrder(self.price)

        self.is_valid = True


class TradeDict(DataDict):
    def __init__(self, data):
        super(TradeDict, self).__init__()
        self.order_id = None
        self.trade_id = None
        self.order_book_id = None

        self.side = None
        self.exchange_id = None
        self.position_effect = None
        self.quantity = None
        self.style = None
        self.price = None

        self.is_valid = False
        
        self.update_data(data)

    def update_data(self, data):
        self.order_id = int(data.OrderRef)
        self.trade_id = data.TradeID
        self.order_book_id = make_order_book_id(data.InstrumentID)

        self.side = SIDE_REVERSE.get(data.Direction, SIDE.BUY)

        self.exchange_id = data.ExchangeID

        if self.exchange_id == 'SHFE':
            if data.OffsetFlag == ApiStruct.OF_Open:
                self.position_effect = POSITION_EFFECT.OPEN
            elif data.OffsetFlag == ApiStruct.OF_CloseToday:
                self.position_effect = POSITION_EFFECT.CLOSE_TODAY
            else:
                self.position_effect = POSITION_EFFECT.CLOSE
        else:
            if data.OffsetFlag == ApiStruct.OF_Open:
                self.position_effect = POSITION_EFFECT.OPEN
            else:
                self.position_effect = POSITION_EFFECT.CLOSE

        self.quantity = data.Volume
        self.price = data.Price
        self.style = LimitOrder(self.price)

        self.is_valid = True
