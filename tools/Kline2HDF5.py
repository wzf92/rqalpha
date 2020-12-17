import os
import datetime
import h5py
import numpy as np

DEFAULT_DTYPE = np.dtype([
    ('datetime', np.int64),
    ('open', np.float),
    ('close', np.float),
    ('high', np.float),
    ('low', np.float),
    ('limit_up', np.float),
    ('limit_down', np.float),
    ('volume', np.float),
    ('total_turnover', np.float),
    ('settlement', np.float),
    ('prev_settlement', np.float),
])


class Kline2HDF5:
    def __init__(self, fo_name):
        self._timeformat = "%Y-%m-%d %H:%M:%S"
        self._create_output_file(fo_name)

    def _create_output_file(self, fo_name):
        self._fo = h5py.File(fo_name, "w")

    def finished(self):
        self._fo.close()

    def translate(self, fi_name, symbol=None):
        print(fi_name, symbol)
        fi = open(fi_name, 'r')
        if not symbol:
            symbol = os.path.basename(fi_name).split('.')[0]
        res = []
        lines = fi.readlines()
        last_dt = None
        for line in lines:
            vars = line.strip('\n').split(',')
            datetime_array = datetime.datetime.fromtimestamp(int(vars[0]))
            if last_dt:
                delta = datetime_array - last_dt
                if delta.days >= 1 and 20 <= datetime_array.hour <= 24:
                    # datetime_array = datetime_array - datetime.timedelta(days=1)
                    datetime_array = datetime_array.replace(day=last_dt.day, month=last_dt.month)
                if datetime_array <= last_dt:
                    print(line)
                    print(datetime_array)
                    print(datetime_array.second)
                    print(last_dt)
                    print(last_dt.hour)
                    assert False
            datetime_str = datetime_array.strftime("%Y%m%d%H%M%S")
            # t = int(vars[0])
            o = float(vars[1])
            h = float(vars[2])
            l = float(vars[3])
            c = float(vars[4])
            v = float(vars[5])
            res.append((datetime_str, o, c, h, l, o * 1.1, o * 0.9, v, -1, -1, -1))
            last_dt = datetime_array
        fi.close()
        res_array = np.asarray(res, dtype=DEFAULT_DTYPE)
        self._fo.create_dataset(symbol, data=res_array)
        return True

if __name__ == '__main__':
    rq2h5 = Kline2HDF5("futures_min_test.h5")
    rq2h5.translate("/Users/zhifeng/rqalpha/data/rqdata/I88-4.csv", "I88")
    rq2h5.finished()
