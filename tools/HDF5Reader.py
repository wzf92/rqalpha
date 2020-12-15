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


class HDF5Reader:
    def __init__(self):
        pass

    def read(self, file_name, key_name):
        f = h5py.File(file_name, 'r')
        print(f.keys())
        print(f.attrs)
        #print('\n'.join(['%s:%s' % item for item in f.__dict__.items()]))

        data = f[key_name]
        print(data.dtype)
        print(data.shape)
        print("first 10:")
        # print(data.value[0:100])
        print(data[0:10])
        print("last 10:")
        # print(data.value[-100:])
        print(data[-10:])
        f.close()

    def test(self, file_name, key_name):
        f = h5py.File(file_name, 'r')
        data = f[key_name]
        fo = h5py.File(file_name + ".out", "w")
        d = fo.create_dataset(key_name, data=data)
        f.close()
        fo.close()
        return d

if __name__ == "__main__":
    reader = HDF5Reader()
    #reader.read('/Users/zhifeng/Projects/rqalpha/data/hdf5/I2003.h5', 'I2003')
    #reader.read('/Users/zhifeng/Projects/rqalpha/data/hdf5/futures.h5', 'I2003')
    #reader.read('/Users/zhifeng/Projects/rqalpha/data/hdf5/futures.h5.out', 'I2003')
    #reader.test('/Users/zhifeng/Projects/rqalpha/data/hdf5/futures.h5', 'I2003')
    #reader.read('/Users/zhifeng/.rqalpha/bundle/output/futures_min.h5', 'I88')
    reader.read('/root/projects/rqalpha/tools/2020-12-15/futures_min.h5', 'I88')
