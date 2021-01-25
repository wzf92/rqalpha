# -*- coding: utf-8 -*-
# 版权所有 2020 深圳米筐科技有限公司（下称“米筐科技”）
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
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Union, Optional, Sequence

import six
import numpy as np
import pandas as pd

from rqalpha.interface import AbstractDataSource
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.datetime_func import convert_date_to_int, convert_int_to_date, convert_date_min_to_int, convert_int_to_datetime
from rqalpha.const import INSTRUMENT_TYPE, TRADING_CALENDAR_TYPE
from rqalpha.model.instrument import Instrument
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.typing import DateLike

from .storage_interface import AbstractInstrumentStore, AbstractCalendarStore, AbstractDayBarStore, AbstractDateSet
from .storages import (
    InstrumentStore, ShareTransformationStore, FutureInfoStore, ExchangeTradingCalendarStore, DateSet, DayBarStore,
    DividendStore, YieldCurveStore, SimpleFactorStore
)
from .adjust import adjust_bars, FIELDS_REQUIRE_ADJUSTMENT


class BaseDataSource(AbstractDataSource):
    def __init__(self, path, custom_future_info):
        if not os.path.exists(path):
            raise RuntimeError('bundle path {} not exist'.format(os.path.abspath(path)))

        def _p(name):
            return os.path.join(path, name)

        funds_day_bar_store = DayBarStore(_p('funds.h5'))
        self._day_bars = {
            INSTRUMENT_TYPE.CS: DayBarStore(_p('stocks.h5')),
            INSTRUMENT_TYPE.INDX: DayBarStore(_p('indexes.h5')),
            INSTRUMENT_TYPE.FUTURE: DayBarStore(_p('futures.h5')),
            # INSTRUMENT_TYPE.CUSTOM_TYPE1: DayBarStore(_p('I88.h5')),
            INSTRUMENT_TYPE.ETF: funds_day_bar_store,
            INSTRUMENT_TYPE.LOF: funds_day_bar_store
        }  # type: Dict[INSTRUMENT_TYPE, AbstractDayBarStore]

        self._min_bars = {
            INSTRUMENT_TYPE.FUTURE: DayBarStore(_p('futures_min.h5'))
        }  # type: Dict[INSTRUMENT_TYPE, AbstractDayBarStore]

        self._future_info_store = FutureInfoStore(_p("future_info.json"), custom_future_info)

        self._instruments = InstrumentStore(
            _p('instruments.pk'), self._future_info_store
        ).get_all_instruments()  # type: List[Instrument]

        dividend_store = DividendStore(_p('dividends.h5'))
        self._dividends = {
            INSTRUMENT_TYPE.CS: dividend_store,
            INSTRUMENT_TYPE.ETF: dividend_store,
            INSTRUMENT_TYPE.LOF: dividend_store,
        }

        self._calendar_providers = {
            TRADING_CALENDAR_TYPE.EXCHANGE: ExchangeTradingCalendarStore(_p("trading_dates.npy"))
        }

        self._yield_curve = YieldCurveStore(_p('yield_curve.h5'))

        split_store = SimpleFactorStore(_p('split_factor.h5'))
        self._split_factors = {
            INSTRUMENT_TYPE.CS: split_store,
            INSTRUMENT_TYPE.ETF: split_store,
            INSTRUMENT_TYPE.LOF: split_store,
        }
        self._ex_cum_factor = SimpleFactorStore(_p('ex_cum_factor.h5'))
        self._share_transformation = ShareTransformationStore(_p('share_transformation.json'))

        self._suspend_days = [DateSet(_p('suspended_days.h5'))]  # type: List[AbstractDateSet]
        self._st_stock_days = DateSet(_p('st_stock_days.h5'))

    def register_day_bar_store(self, instrument_type, store):
        #  type: (INSTRUMENT_TYPE, AbstractDayBarStore) -> None
        self._day_bars[instrument_type] = store

    def register_instruments_store(self, instruments_store):
        # type: (AbstractInstrumentStore) -> None
        self._instruments.extend(instruments_store.get_all_instruments())

    def register_dividend_store(self, instrument_type, dividend_store):
        # type: (INSTRUMENT_TYPE, DividendStore) -> None
        self._dividends[instrument_type] = dividend_store

    def register_split_store(self, instrument_type, split_store):
        self._split_factors[instrument_type] = split_store

    def register_calendar_store(self, calendar_type, calendar_store):
        # type: (TRADING_CALENDAR_TYPE, AbstractCalendarStore) -> None
        self._calendar_providers[calendar_type] = calendar_store

    def append_suspend_date_set(self, date_set):
        # type: (AbstractDateSet) -> None
        self._suspend_days.append(date_set)

    def get_dividend(self, instrument):
        try:
            dividend_store = self._dividends[instrument.type]
        except KeyError:
            return None

        return dividend_store.get_dividend(instrument.order_book_id)

    def get_trading_minutes_for(self, order_book_id, trading_dt):
        # 每日交易时间细化 @TODO
        res = []

        # 00:00 - 02:30
        start_dt = trading_dt.replace(hour = 9, minute = 1)
        end_dt = trading_dt.replace(hour = 10, minute = 15)
        cur_dt = start_dt
        while cur_dt <= end_dt:
            res.append(cur_dt)
            cur_dt = cur_dt + timedelta(minutes = 1)

        # 09:01 - 10:15
        start_dt = trading_dt.replace(hour = 9, minute = 1)
        end_dt = trading_dt.replace(hour = 10, minute = 15)
        cur_dt = start_dt
        while cur_dt <= end_dt:
            res.append(cur_dt)
            cur_dt = cur_dt + timedelta(minutes = 1)

        # 10:31 - 11:30
        start_dt = trading_dt.replace(hour=10, minute=31)
        end_dt = trading_dt.replace(hour=11, minute=30)
        cur_dt = start_dt
        while cur_dt <= end_dt:
            res.append(cur_dt)
            cur_dt = cur_dt + timedelta(minutes=1)

        # 13:31 - 15:00
        start_dt = trading_dt.replace(hour=13, minute=31)
        end_dt = trading_dt.replace(hour=15, minute=0)
        cur_dt = start_dt
        while cur_dt <= end_dt:
            res.append(cur_dt)
            cur_dt = cur_dt + timedelta(minutes=1)

        # 21: 01 - 23:59
        start_dt = trading_dt.replace(hour=21, minute=1)
        end_dt = trading_dt.replace(hour=23, minute=59)
        cur_dt = start_dt
        while cur_dt <= end_dt:
            res.append(cur_dt)
            cur_dt = cur_dt + timedelta(minutes = 1)

        return res
        # raise NotImplementedError

    def get_trading_calendars(self):
        # type: () -> Dict[TRADING_CALENDAR_TYPE, pd.DatetimeIndex]
        return {t: store.get_trading_calendar() for t, store in self._calendar_providers.items()}

    def get_all_instruments(self):
        return self._instruments

    def get_share_transformation(self, order_book_id):
        return self._share_transformation.get_share_transformation(order_book_id)

    def is_suspended(self, order_book_id, dates):
        # type: (str, Sequence[DateLike]) -> List[bool]
        for date_set in self._suspend_days:
            result = date_set.contains(order_book_id, dates)
            if result is not None:
                return result
        else:
            return [False] * len(dates)

    def is_st_stock(self, order_book_id, dates):
        result = self._st_stock_days.contains(order_book_id, dates)
        return result if result is not None else [False] * len(dates)

    @lru_cache(None)
    def _all_day_bars_of(self, instrument):
        return self._day_bars[instrument.type].get_bars(instrument.order_book_id)

    @lru_cache(None)
    def _filtered_day_bars(self, instrument):
        bars = self._all_day_bars_of(instrument)
        return bars[bars['volume'] > 0]

    @lru_cache(maxsize=4)
    def _all_min_bars_of(self, instrument, dt_start=None, dt_end=None):
        return self._min_bars[instrument.type].get_bars(instrument.order_book_id, dt_start, dt_end)

    @lru_cache(maxsize=4)
    def _filtered_min_bars(self, instrument):
        bars = self._all_min_bars_of(instrument)
        return bars[bars['volume'] > 0]

    def _history_merge_min_bar(self, bars):
        DEFAULT_DTYPE = np.dtype([
            ('datetime', np.uint64),
            ('open', np.float),
            ('close', np.float),
            ('high', np.float),
            ('low', np.float),
            ('volume', np.float),
        ])

#        print(bars)
        if len(bars) <= 0:
            return None

        merge_open_price = bars[0]['open']
        merge_high_price = bars[0]['high']
        merge_low_price = bars[0]['low']
        merge_close_price = bars[-1]['close']
        merge_volume = 0
        for pos in range(0, len(bars)):
            if bars[pos]['high'] > merge_high_price:
                merge_high_price = bars[pos]['high']
            if bars[pos]['low'] < merge_low_price:
                merge_low_price = bars[pos]['low']
            merge_volume += bars[pos]['volume']
        new_array = np.array([(bars['datetime'][-1], merge_open_price, merge_close_price, merge_high_price, merge_low_price, merge_volume)], dtype=DEFAULT_DTYPE)
#        print(new_array)
        return new_array[0]


    def _merge_min_bar(self, dt, bars, cnt):
        DEFAULT_DTYPE = np.dtype([
            ('datetime', np.uint64),
            ('open', np.float),
            ('close', np.float),
            ('high', np.float),
            ('low', np.float),
            ('volume', np.float),
        ])

        dt_merge_start = np.uint64(convert_date_min_to_int(dt - timedelta(minutes=cnt-1)))
        dt_merge_end = np.uint64(convert_date_min_to_int(dt))
        pos_merge_start = bars['datetime'].searchsorted(dt_merge_start)
        pos_merge_end = bars['datetime'].searchsorted(dt_merge_end)
        if pos_merge_end >= len(bars) or bars['datetime'][pos_merge_end] != dt_merge_end:
            return None
        merge_open_price = bars[pos_merge_start]['open']
        merge_high_price = bars[pos_merge_start]['high']
        merge_low_price = bars[pos_merge_start]['low']
        merge_close_price = bars[pos_merge_end]['close']
        merge_volume = 0
        for pos in range(pos_merge_start, pos_merge_end + 1):
            if bars[pos]['high'] > merge_high_price:
                merge_high_price = bars[pos]['high']
            if bars[pos]['low'] < merge_low_price:
                merge_low_price = bars[pos]['low']
            merge_volume += bars[pos]['volume']
        new_array = np.array([(dt_merge_end, merge_open_price, merge_close_price, merge_high_price, merge_low_price, merge_volume)], dtype=DEFAULT_DTYPE)
        return new_array[0]


    def get_bar(self, instrument, dt, frequency):
        # type: (Instrument, Union[datetime, date], str) -> Optional[np.ndarray]
        if frequency not in ['1d', '1m', '5m', '15m']:
            raise NotImplementedError
        if frequency == '1d':
            bars = self._all_day_bars_of(instrument)
            if len(bars) <= 0:
                return
            dt = np.uint64(convert_date_to_int(dt))
            pos = bars['datetime'].searchsorted(dt)
            if pos >= len(bars) or bars['datetime'][pos] != dt:
                return None
            return bars[pos]
        elif frequency == '1m':
            dt_day_start = np.uint64(convert_date_to_int(dt))
            dt_day_end = np.uint64(convert_date_to_int(dt + timedelta(days=1)))
            bars = self._all_min_bars_of(instrument, dt_day_start, dt_day_end)
            if len(bars) <= 0:
                return
            dt = np.uint64(convert_date_min_to_int(dt))
            pos = bars['datetime'].searchsorted(dt)
            if pos >= len(bars) or bars['datetime'][pos] != dt:
                return None
            return bars[pos]
        elif frequency == '5m':
            dt_day_start = np.uint64(convert_date_to_int(dt))
            dt_day_end = np.uint64(convert_date_to_int(dt + timedelta(days=1)))
            bars = self._all_min_bars_of(instrument, dt_day_start, dt_day_end)
            if len(bars) <= 0:
                return
            merge_bar = self._merge_min_bar(dt, bars, 5)
            return merge_bar
        elif frequency == '15m':
            dt_day_start = np.uint64(convert_date_to_int(dt))
            dt_day_end = np.uint64(convert_date_to_int(dt + timedelta(days=1)))
            bars = self._all_min_bars_of(instrument, dt_day_start, dt_day_end)
            if len(bars) <= 0:
                return
            merge_bar = self._merge_min_bar(dt, bars, 15)
            return merge_bar

    def get_settle_price(self, instrument, date):
        bar = self.get_bar(instrument, date, '1d')
        if bar is None:
            return np.nan
        return bar['settlement']

    @staticmethod
    def _are_fields_valid(fields, valid_fields):
        if fields is None:
            return True
        if isinstance(fields, six.string_types):
            return fields in valid_fields
        for field in fields:
            if field not in valid_fields:
                return False
        return True

    def get_ex_cum_factor(self, order_book_id):
        return self._ex_cum_factor.get_factors(order_book_id)

    def history_bars(self, instrument, bar_count, frequency, fields, dt,
                     skip_suspended=True, include_now=False,
                     adjust_type='pre', adjust_orig=None):
        if frequency not in ['1m', '5m', '15m', '1d']:
            raise NotImplementedError

        if skip_suspended and instrument.type == 'CS':
            bars = self._filtered_day_bars(instrument)
        elif frequency == '1d':
            bars = self._all_day_bars_of(instrument)
        elif frequency in ['1m', '5m', '15m']:
            dt_end = np.uint64(convert_date_to_int(dt + timedelta(days=1)))
            dt_start = np.uint(convert_date_to_int(dt - timedelta(days=int(bar_count/180) + 30))) # @TODO
            bars = self._all_min_bars_of(instrument, dt_start, dt_end)

        if not self._are_fields_valid(fields, bars.dtype.names):
            raise RQInvalidArgument("invalid fileds: {}".format(fields))

        if len(bars) <= 0:
            return bars

        if frequency == '1d':
            dt = np.uint64(convert_date_to_int(dt))
        elif frequency in ['1m', '5m', '15m']:
            dt = np.uint64(convert_date_min_to_int(dt))

        count = int(frequency[:-1])
        i = bars['datetime'].searchsorted(dt, side='right')
        if i <= 0:
            return None
        left = i - bar_count * count if i >= bar_count * count else 0
        if count > 1:
            merge_bars = []
            for j in range(0, bar_count):
                if left + (j+1) * count > i:
                    break;
                merge_bar = self._history_merge_min_bar(bars[left + j * count:left + (j+1) * count])
                merge_bars.append(merge_bar)
            bars = np.array(merge_bars)
        else:
            bars = bars[left:i]
        if adjust_type == 'none' or instrument.type in {'Future', 'INDX'}:
            # 期货及指数无需复权
            return bars if fields is None else bars[fields]

        if isinstance(fields, str) and fields not in FIELDS_REQUIRE_ADJUSTMENT:
            return bars if fields is None else bars[fields]

        return adjust_bars(bars, self.get_ex_cum_factor(instrument.order_book_id),
                           fields, adjust_type, adjust_orig)

    def current_snapshot(self, instrument, frequency, dt):
        raise NotImplementedError

    def get_split(self, instrument):
        try:
            splilt_store = self._split_factors[instrument.type]
        except KeyError:
            return None

        return splilt_store.get_factors(instrument.order_book_id)

    def available_data_range(self, frequency):
        # FIXME
        from rqalpha.environment import Environment
        from rqalpha.const import DEFAULT_ACCOUNT_TYPE
        accounts = Environment.get_instance().config.base.accounts
        if not (DEFAULT_ACCOUNT_TYPE.STOCK in accounts or DEFAULT_ACCOUNT_TYPE.FUTURE in accounts):
            return date.min, date.max
        if frequency in ['tick', '1d', '1m', '5m', '15m', '30m']:
            #s, e = self._day_bars[INSTRUMENT_TYPE.INDX].get_date_range('000001.XSHG')
            s = "20100101000000"
            e = "20991231000000"
            return convert_int_to_date(s).date(), convert_int_to_date(e).date()

    def get_ticks(self, order_book_id, date):
        raise NotImplementedError

    def get_yield_curve(self, start_date, end_date, tenor=None):
        return self._yield_curve.get_yield_curve(start_date, end_date, tenor=tenor)

    def get_commission_info(self, instrument):
        return self._future_info_store.get_future_info(instrument)

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        raise NotImplementedError

    def history_ticks(self, instrument, count, dt):
        raise NotImplementedError
