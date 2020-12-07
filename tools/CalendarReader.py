import numpy as np
import pandas


class CalendarReader:
    def __init__(self):
        pass

    def read(self, filename):
        return pandas.to_datetime([str(d) for d in np.load(filename, allow_pickle=False)])


if __name__ == "__main__":
    cr = CalendarReader()
    data = cr.read("/Users/zhifeng/.rqalpha/bundle/trading_dates.npy")
    print(data)