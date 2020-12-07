import sys
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

class RQData2HDF5:
    def __init__(self):
        self._timeformat = "%Y-%m-%d %H:%M:%S"
        pass

    def translate(self, fi_name, fo_name, symbol = None):
        fi = open(fi_name, 'r')
        fo = h5py.File(fo_name,"w")
        if not symbol:
            symbol = os.path.basename(fi_name).split('.')[0]
        res = []
        lines = fi.readlines()
        t_i = -1
        o_i = -1
        h_i = -1
        l_i = -1
        c_i = -1
        v_i = -1
        header_line = lines[0]
        header_vars = header_line.strip('\n').split(',')
        for i in range(0, len(header_vars)):
            if header_vars[i] == "datetime":
                t_i = i
            elif header_vars[i] == "open":
                o_i = i
            elif header_vars[i] == "high":
                h_i = i
            elif header_vars[i] == "low":
                l_i = i
            elif header_vars[i] == "close":
                c_i = i
            elif header_vars[i] == "volume":
                v_i = i
        for line in lines[1:]:
            vars = line.strip('\n').split(',')
            # datetime_array = datetime.datetime.fromtimestamp(int(v[0]))
            datetime_array = datetime.datetime.strptime(vars[t_i], self._timeformat)
            datetime_str = datetime_array.strftime("%Y%m%d%H%M%S")
            o = float(vars[o_i])
            h = float(vars[h_i])
            l = float(vars[l_i])
            c = float(vars[c_i])
            v = float(vars[v_i])
            res.append((datetime_str, o, c, h, l, o * 1.1, o * 0.9, v, -1, -1, -1))
        fi.close()
        res_array = np.asarray(res, dtype=DEFAULT_DTYPE)
        d = fo.create_dataset(symbol, data=res_array)
        fo.close()
        return True

if __name__ == '__main__':
    rq2h5 = RQData2HDF5()
    rq2h5.translate("/Users/zhifeng/Projects/rqalpha/data/rqdata/I2003.csv", "/Users/zhifeng/Projects/rqalpha/data/hdf5/I2003.h5")