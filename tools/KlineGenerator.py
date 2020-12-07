import sys
import os
import time, datetime
import platform

class KlineGenerator:
    def __init__(self, file_list):
        self._file_list = file_list

    def all_path(self, dirname):
        result = []
        for maindir, subdir, file_name_list in os.walk(dirname):
            break
        for filename in file_name_list:
            if 'all' in self._file_list or filename in self._file_list:
                apath = os.path.join(maindir, filename)#合并成一个完整路径
                result.append(apath)
        return result

    def get_timestamp(self, t_str, ts):
        t = int(time.mktime(time.strptime(t_str, "%Y-%m-%d %H:%M:%S")))
        t = int(t/ts)*ts
        return t

    def klines(self, fi, fo, fd, ts=60):
        init_index = False
        t_index = 0
        o_index = -1
        h_index = -1
        l_index = -1
        c_index = -1
        v_index = -1
        oi_index = -1
        dominant_list = fd.readline().strip('\n').split(',')
        for v_str in fi.readlines():
            if init_index == False:
                label = v_str.strip('\n').split(',')
                for i,l in enumerate(label):
                    if l == 'open':
                        o_index = i
                    elif l == 'high':
                        h_index = i
                    elif l == 'low':
                        l_index = i
                    elif l == 'close':
                        c_index = i
                    elif l == 'volume':
                        v_index = i
                    elif l == 'open_interest':
                        oi_index = i
                if o_index < 0 or h_index < 0 or l_index < 0 or c_index < 0 or v_index < 0 or oi_index < 0:
                    print("parse label failed. %d,%d,%d,%d,%d,%d" % (o_index,h_index,l_index,c_index,v_index,oi_index))
                    exit(0)
                else:
                    init_index = True
                    continue
            v = v_str.strip('\n').split(',')
            t_str = v[0]
            date_str = v[0].split(' ')[0]
            while dominant_list[0] < date_str:
                dominant_list = fd.readline().strip('\n').split(',')
            if date_str != dominant_list[0]:
                #print('%s != %s' % (date_str, dominant_list[0]))
                #exit(1)
                pass
            t = self.get_timestamp(t_str, 60)
            v_o = str(round(float(v[o_index]), 4))
            v_h = str(round(float(v[h_index]), 4))
            v_l = str(round(float(v[l_index]), 4))
            v_c = str(round(float(v[c_index]), 4))
            v_v = str(round(float(v[v_index]), 4))
            v_oi = str(round(float(v[oi_index]), 4))
            out_str = ','.join(([str(t),v_o,v_h,v_l,v_c,v_v,v_oi,dominant_list[1]]))
            fo.write(out_str + '\n')

    def run(self):
        in_dir = 'input'
        out_dir = 'data'
        in_files = self.all_path(in_dir)
        for fi_name in in_files:
            print(fi_name)
            fi = open(fi_name, 'r')
            if (platform.system() == 'Windows'):
                last_name = fi_name.split('\\')[-1]
            else:
                last_name = fi_name.split('/')[-1]
            if last_name.find('dominant') >= 0:
                fi.close()
                continue
            future_name = last_name.split('.')[0]
            if (platform.system() == 'Windows'):
                dominant_name = in_dir + '\\' + future_name + '_dominant.csv'
            else:
                dominant_name = in_dir + '/' + future_name + '_dominant.csv'
            fd = open(dominant_name, 'r')
            fo_name = os.path.join(out_dir, last_name)
            fo = open(fo_name, 'w')
            self.klines(fi, fo, fd)
            fi.close()
            fo.close()

