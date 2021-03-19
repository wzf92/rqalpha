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

import sys
from functools import wraps
from rqalpha.const import ORDER_TYPE, SIDE, POSITION_EFFECT

#from .pyctp import MdApi, TraderApi, ApiStruct
from .data_dict import TickDict, PositionDict, AccountDict, InstrumentDict, OrderDict, TradeDict, CommissionDict
from ..utils import make_order_book_id, str2bytes, bytes2str

from ctpwrapper import ApiStructure
from ctpwrapper import MdApiPy
from ctpwrapper import TraderApiPy
from . import CtpDefines

ORDER_TYPE_MAPPING = {
    ORDER_TYPE.MARKET: CtpDefines.OPT_AnyPrice,
    ORDER_TYPE.LIMIT: CtpDefines.OPT_LimitPrice,
}

SIDE_MAPPING = {
    SIDE.BUY: CtpDefines.D_Buy,
    SIDE.SELL: CtpDefines.D_Sell,
}

POSITION_EFFECT_MAPPING = {
    POSITION_EFFECT.OPEN: CtpDefines.OF_Open,
    POSITION_EFFECT.CLOSE: CtpDefines.OF_Close,
    POSITION_EFFECT.CLOSE_TODAY: CtpDefines.OF_CloseToday,
}

def query_in_sync(func):
    @wraps(func)
    def wrapper(api, pData, pRspInfo, nRequestID, bIsLast):
        api._req_id = max(api.req_id, nRequestID)
        result = func(api, pData, pRspInfo, nRequestID, bIsLast)
        if bIsLast:
            api.gateway.on_query(api.api_name, nRequestID, result)
    return wrapper

class CtpMdApi(MdApiPy):
    def __init__(self, gateway, user_id, password, broker_id, address, api_name='ctp_md'):
        super(CtpMdApi, self).__init__()

        self.gateway = gateway
        self._req_id = 0

        self.connected = False
        self.logged_in = False

        self.user_id = user_id
        self.password = password
        self.broker_id = broker_id
        self.address = address

        self.api_name = api_name

    def OnFrontConnected(self):
        """服务器连接"""
        self.connected = True
        self.login()

    def OnFrontDisconnected(self, nReason):
        """服务器断开"""
        self.connected = False
        self.logged_in = False
        self.gateway.on_debug('服务器断开，将自动重连。')

    def OnHeartBeatWarning(self, nTimeLapse):
        """心跳报警"""
        pass

    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        """错误回报"""
        self.gateway.on_err(pRspInfo, sys._getframe().f_code.co_name)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登陆回报"""
        if pRspInfo.ErrorID == 0:
            self.logged_in = True
        else:
            self.gateway.on_err(pRspInfo, sys._getframe().f_code.co_name)

    def OnRspUserLogout(self, pUserLogout, pRspInfo, nRequestID, bIsLast):
        """登出回报"""
        if pRspInfo.ErrorID == 0:
            self.logged_in = False
        else:
            self.gateway.on_err(pRspInfo, sys._getframe().f_code.co_name)

    def OnRspSubMarketData(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        """订阅合约回报"""
        print("OnRspSubMarketData")
        print(pSpecificInstrument)
        print(pRspInfo)
        pass

    def OnRspUnSubForQuoteRsp(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        """退订合约回报"""
        pass

    def OnRtnDepthMarketData(self, pDepthMarketData):
        """行情推送"""
        print("OnRtnDepthMarketData")
        tick_dict = TickDict(pDepthMarketData)
        print(tick_dict)
        if tick_dict.is_valid:
            self.gateway.on_tick(tick_dict)

    def OnRspSubForQuoteRsp(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        """订阅期权询价"""
        pass

    def OnRspUnSubMarketData(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        """退订期权询价"""
        pass

    def OnRtnForQuoteRsp(self, pForQuoteRsp):
        """期权询价推送"""
        pass

    @property
    def req_id(self):
        self._req_id += 1
        return self._req_id

    def connect(self):
        """初始化连接"""
        if not self.connected:
            self.Create()
            #self.RegisterFront(str2bytes(self.address))
            self.RegisterFront(self.address)
            self.Init()
        else:
            self.login()

    def subscribe(self, ins_id_list):
        """订阅合约"""
        if len(ins_id_list) > 0:
            #ins_id_list = [str2bytes(i) for i in ins_id_list]
            ins_id_list = ['SN2106']
            self.SubscribeMarketData(ins_id_list)

    def login(self):
        """登录"""
        if not self.logged_in:
            req = ApiStructure.ReqUserLoginField(BrokerID=self.broker_id,
                                         UserID=self.user_id,
                                         Password=self.password)
            req_id = self.req_id
            self.ReqUserLogin(req, req_id)
            return req_id

    def close(self):
        """关闭"""
        pass
        # self.Join()


class CtpTdApi(TraderApiPy):
    def __init__(self, gateway, user_id, password, broker_id, address, auth_code, user_production_info, api_name='ctp_td'):
        super(CtpTdApi, self).__init__()

        self.gateway = gateway
        self._req_id = 0

        self.connected = False
        self.logged_in = False
        #self.authenticated = False
        self.authenticated = True

        self.user_id = user_id
        self.password = password
        self.broker_id = broker_id
        self.address = address

        self.auth_code = auth_code
        self.user_production_info = user_production_info

#        self.broker_id = broker_id
#        self.investor_id = investor_id
#        self.password = password
#        self.auth_code = auth_code
#        self.app_id = app_id

        self.front_id = 0
        self.session_id = 0

        self.require_authentication = True

        self.pos_cache = {}
        self.ins_cache = {}
        self.order_cache = {}

        self.api_name = api_name

    def OnFrontConnected(self):
        print("OnFrontConnected")
        self.connected = True
        if self.require_authentication:
            self.authenticate()
        else:
            self.login()

    def OnFrontDisconnected(self, nReason):
        self.connected = False
        self.logged_in = False
        self.gateway.on_debug('服务器断开，将自动重连。')

    def OnHeartBeatWarning(self, nTimeLapse):
        """心跳报警"""
        pass

    def OnRspAuthenticate(self, pRspAuthenticate, pRspInfo, nRequestID, bIsLast):
        """验证客户端回报"""
        print("OnRspAuthenticate")
        if pRspInfo.ErrorID == 0:
            self.authenticated = True
            self.login()
        else:
            self.gateway.on_err(pRspInfo, sys._getframe().f_code.co_name)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登陆回报"""
        print("OnRspUserLogin")
        if pRspInfo.ErrorID == 0:
            self.front_id = pRspUserLogin.FrontID
            self.session_id = pRspUserLogin.SessionID
            self.logged_in = True
            self.qrySettlementInfoConfirm()
        else:
            self.gateway.on_err(pRspInfo, sys._getframe().f_code.co_name)

    def OnRspUserLogout(self, pUserLogout, pRspInfo, nRequestID, bIsLast):
        """登出回报"""
        if pRspInfo.ErrorID == 0:
            self.logged_in = False
        else:
            self.gateway.on_err(pRspInfo)

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        order_dict = OrderDict(pInputOrder, rejected=True)
        if order_dict.is_valid:
            self.gateway.on_order(order_dict)

    def OnRspOrderAction(self, pInputOrderAction, pRspInfo, nRequestID, bIsLast):
        self.gateway.on_err(pRspInfo, sys._getframe().f_code.co_name)

    @query_in_sync
    def OnRspQryOrder(self, pOrder, pRspInfo, nRequestID, bIsLast):
        """报单回报"""
        if pOrder:
            order_dict = OrderDict(pOrder)
            if order_dict.is_valid:
                self.order_cache[order_dict.order_id] = order_dict
        if bIsLast:
            return self.order_cache

    @query_in_sync
    def OnRspQryInvestorPosition(self, pInvestorPosition, pRspInfo, nRequestID, bIsLast):
        """持仓查询回报"""
        if pInvestorPosition is None:
            return self.pos_cache

        if pInvestorPosition.InstrumentID:
            order_book_id = make_order_book_id(pInvestorPosition.InstrumentID)
            if order_book_id not in self.pos_cache:
                self.pos_cache[order_book_id] = PositionDict(pInvestorPosition)
            else:
                self.pos_cache[order_book_id].update_data(pInvestorPosition)
        if bIsLast:
            return self.pos_cache

    @query_in_sync
    def OnRspQryTradingAccount(self, pTradingAccount, pRspInfo, nRequestID, bIsLast):
        """资金账户查询回报"""
        return AccountDict(pTradingAccount)

    @query_in_sync
    def OnRspQryInstrumentCommissionRate(self, pInstrumentCommissionRate, pRspInfo, nRequestID, bIsLast):
        """请求查询合约手续费率响应"""
        return CommissionDict(pInstrumentCommissionRate)

    @query_in_sync
    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        """合约查询回报"""
        ins_dict = InstrumentDict(pInstrument)
        if ins_dict.is_valid:
            self.ins_cache[ins_dict.order_book_id] = ins_dict
        if bIsLast:
            return self.ins_cache

    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        """错误回报"""
        self.gateway.on_err(pRspInfo, sys._getframe().f_code.co_name)

    def OnRtnOrder(self, pOrder):
        """报单回报"""
        order_dict = OrderDict(pOrder)
        if order_dict.is_valid:
            self.gateway.on_order(order_dict)

    def OnRtnTrade(self, pTrade):
        """成交回报"""
        trade_dict = TradeDict(pTrade)
        self.gateway.on_trade(trade_dict)

    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        """发单错误回报（交易所）"""
        self.gateway.on_err(pRspInfo, sys._getframe().f_code.co_name)
        order_dict = OrderDict(pInputOrder)
        if order_dict.is_valid:
            self.gateway.on_order(order_dict)

    def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
        """撤单错误回报（交易所）"""
        self.gateway.on_err(pRspInfo, sys._getframe().f_code.co_name)

    @property
    def req_id(self):
        self._req_id += 1
        return self._req_id

    def connect(self):
        if not self.connected:
            self.Create()
            #self.SubscribePrivateTopic(0)
            #self.SubscribePublicTopic(0)
            #self.RegisterFront(str2bytes(self.address))
            print("SubscribePrivateTopic")
            self.SubscribePrivateTopic(2)
            print("SubscribePublicTopic")
            self.SubscribePublicTopic(2)
            print("RegisterFront")
            self.RegisterFront(self.address)
            print("Init")
            self.Init()
        else:
            if self.require_authentication:
                self.authenticate()
            else:
                self.login()

    def authenticate(self):
        """申请验证"""
        print("authenticate")
        if self.authenticated:
#            req = ApiStructure.AuthenticationInfo(
#                BrokerID=self.broker_id,
#                UserID=self.user_id,
#                AuthInfo=self.auth_code,
#                UserProductInfo=self.user_production_info
#            )
            req = ApiStructure.ReqAuthenticateField(BrokerID=self.broker_id,
                                                    AuthCode=self.auth_code,
                                                    AppID=self.user_production_info)
            req_id = self.req_id
            print('验证: ' + str(req))
            self.ReqAuthenticate(req, req_id)
            return req_id
        else:
            self.login()

    def login(self):
        """登录"""
        print("login")
        if not self.logged_in:
            req = ApiStructure.ReqUserLoginField(
                UserID=self.user_id,
                BrokerID=self.broker_id,
                Password=self.password,
            )
            print(req)
            req_id = self.req_id
            self.ReqUserLogin(req, req_id)
            return req_id

    def qrySettlementInfoConfirm(self):
        #req = ApiStructure.SettlementInfoConfirm(BrokerID=str2bytes(self.broker_id), InvestorID=str2bytes(self.user_id))
        req = ApiStructure.SettlementInfoConfirmField.from_dict({"BrokerID": self.broker_id,
                                                                 "InvestorID": self.user_id})
        req_id = self.req_id
        self.ReqSettlementInfoConfirm(req, req_id)

    def qryInstrument(self):
        self.ins_cache = {}
        req = ApiStructure.QryInstrumentField()
        req_id = self.req_id
        self.ReqQryInstrument(req, req_id)
        return req_id

    def qryCommission(self, order_book_id):
        ins_dict = self.gateway.get_ins_dict(order_book_id)
        if ins_dict is None:
            return None
        req = ApiStructure.QryInstrumentCommissionRateField(
            InstrumentID=str2bytes(ins_dict.instrument_id),
            InvestorID=str2bytes(self.user_id),
            BrokerID=str2bytes(self.broker_id),
        )
        req_id = self.req_id
        self.ReqQryInstrumentCommissionRate(req, req_id)
        return req_id

    def qryAccount(self):
        req = ApiStructure.QryTradingAccountField(
                BrokerID=str2bytes(self.broker_id),
                InvestorID=str2bytes(self.user_id)
                )
        req_id = self.req_id
        self.ReqQryTradingAccount(req, req_id)
        return req_id

    def qryPosition(self):
        self.pos_cache = {}
        req = ApiStructure.QryInvestorPositionField(
            BrokerID=str2bytes(self.broker_id),
            InvestorID=str2bytes(self.user_id)
        )
        req_id = self.req_id
        self.ReqQryInvestorPosition(req, req_id)
        return req_id

    def qryOrder(self):
        self.order_cache = {}
        req = ApiStructure.QryOrderField(
            BrokerID=str2bytes(self.broker_id),
            InvestorID=str2bytes(self.user_id)
        )
        req_id = self.req_id
        self.ReqQryOrder(req, req_id)
        return req_id

    def sendOrder(self, order):
        ins_dict = self.gateway.get_ins_dict(order.order_book_id)
        if ins_dict is None:
            return None
        req = ApiStructure.InputOrder(
            InstrumentID=str2bytes(ins_dict.instrument_id),
            LimitPrice=str2bytes(order.price),
            VolumeTotalOriginal=str2bytes(order.quantity),
            OrderPriceType=ORDER_TYPE_MAPPING.get(order.type, ''),
            Direction=SIDE_MAPPING.get(order.side, ''),
            CombOffsetFlag=POSITION_EFFECT_MAPPING.get(order.position_effect, ''),

            OrderRef=str2bytes(str(order.order_id)),
            InvestorID=str2bytes(self.user_id),
            UserID=str2bytes(self.user_id),
            BrokerID=str2bytes(self.broker_id),

            CombHedgeFlag=ApiStructure.HF_Speculation,
            ContingentCondition=ApiStructure.CC_Immediately,
            ForceCloseReason=ApiStructure.FCC_NotForceClose,
            IsAutoSuspend=0,
            TimeCondition=ApiStructure.TC_GFD,
            VolumeCondition=ApiStructure.VC_AV,
            MinVolume=1,
        )
        req_id = self.req_id
        self.ReqOrderInsert(req, req_id)
        return self.req_id

    def cancelOrder(self, order):
        ins_dict = self.gateway.get_ins_dict(order.order_book_id)
        if ins_dict is None:
            return None

        req = ApiStructure.InputOrderAction(
            InstrumentID=str2bytes(ins_dict.instrument_id),
            ExchangeID=str2bytes(ins_dict.exchange_id),
            OrderRef=str2bytes(str(order.order_id)),
            FrontID=int(self.front_id),
            SessionID=int(self.session_id),

            ActionFlag=ApiStructure.AF_Delete,
            BrokerID=str2bytes(self.broker_id),
            InvestorID=str2bytes(self.user_id),
        )
        req_id = self.req_id
        self.ReqOrderAction(req, req_id)
        return req_id

    def close(self):
        pass
        # self.Join()