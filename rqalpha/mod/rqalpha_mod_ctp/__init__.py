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


__config__ = {
    "login": {
        'user_id': "85012173",
        'password': "1330840aA",
        'broker_id': "8080",
        'auth_code': "PRDCTCXGFOMWPTPA",
        'user_production_info': "client_ctplq235_3.0"
    },
    "event": {
        "enabled": True,
        "all_day": False,
        "address": "tcp://180.168.212.238:41214",
    },
    "trade": {
        "enabled": True,
        "address": "tcp://180.168.212.238:41206",
    },
}


def load_mod():
    from .mod import CtpMod
    return CtpMod()
