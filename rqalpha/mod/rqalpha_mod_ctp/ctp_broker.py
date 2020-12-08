#!/usr/bin/env python
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

from rqalpha.events import EVENT, Event
from rqalpha.interface import AbstractBroker


class CtpBroker(AbstractBroker):
    def __init__(self, env, trade_gateway):
        super(CtpBroker, self).__init__()
        self._env = env
        self._trade_gateway = trade_gateway
        self._open_orders = []

    def after_trading(self):
        pass

    def before_trading(self):
        self._trade_gateway.connect()
        for account, order in self._trade_gateway.open_orders:
            order.active()
            self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))

    def get_open_orders(self, order_book_id=None):
        if order_book_id is not None:
            return [order for order in self._trade_gateway.open_orders if order.order_book_id == order_book_id]
        else:
            return self._trade_gateway.open_orders

    def submit_order(self, order):
        self._trade_gateway.submit_order(order)

    def cancel_order(self, order):
        self._trade_gateway.cancel_order(order)

    def get_portfolio(self):
        return self._trade_gateway.get_portfolio()

