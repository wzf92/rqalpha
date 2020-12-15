import h5py
import pymongo
import os
import datetime
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


class DumpHDF5:
    def __init__(self, host = "localhost", port = 27017):
        self._timeformat = "%Y-%m-%d %H:%M:%S"
        self._server_addr = "mongodb://%s:%d/" % (host, port)
        self._connect_server()

    def _connect_server(self):
        self._client = pymongo.MongoClient(self._server_addr)

    def dump(self, outdir, db, symbol = ["ALL"], date_start = None, date_end = None):
        db_list = self._client.list_database_names()
        if db not in db_list:
            return False
        db_data = self._client[db]
        h5_out_path = os.path.join(outdir, db + ".h5")
        h5_out = h5py.File(h5_out_path, "w")
        collection_list = db_data.list_collection_names()
        print("collection_list: %s" % str(collection_list))
        find_all = True if symbol[0] == "ALL" else False
        for collection in collection_list:
            if not find_all and collection not in collection_list:
                continue
            print("proc %s..." % collection)
            arrays = []
            collection_data = db_data[collection]
            for record in collection_data.find():
                #print(record)
                datetime_array = datetime.datetime.strptime(record["datetime"], self._timeformat)
                datetime_str = datetime_array.strftime("%Y%m%d%H%M%S")
                o = float(record["open"])
                c = float(record["close"])
                h = float(record["high"])
                l = float(record["low"])
                v = float(record["volume"])
                total_turnover = float(record["total_turnover"])
                arrays.append((datetime_str, o, c, h, l, o * 1.1, o * 0.9, v, total_turnover, -1, -1))
            res_arrays = np.asarray(arrays, dtype = DEFAULT_DTYPE)
            h5_out.create_dataset(collection, data = res_arrays)
        h5_out.close()
        return True


if __name__ == "__main__":
    #dumper = DumpHDF5()
    #dumper.dump(outdir = "/Users/zhifeng/.rqalpha/bundle/output", db = "futures_min")
    dumper = DumpHDF5('localhost', 9999)
    dumper.dump(outdir = "/tmp", db = "futures_min")
