# 数据库
## 概述
使用mongodb来构建我们自己的数据库
目前已导入的数据有:  

- IH88
- IC88
- IF88
- AL88
- AU88
- CU88
- I88
- J88
- RB88
- RU88
- SC88
- SM88
- ZN88

## 浏览数据库
只是浏览数据库的话，推荐使用[MongoDB Compass](https://www.mongodb.com/try/download/compass)  
下载安装完后，打开后界面：  
![mongdb\_1](http://121.40.85.7/mongodb_1.png)
点击**Fill in connection fields individually**，出现界面：
![mongdb\_2](http://121.40.85.7/mongodb_2.png)
按照图中所示填写信息(密码和机器的登陆密码一样)，点击**CONNECT**，就能连接数据库。
数据页面：  
![mongdb\_3](http://121.40.85.7/mongodb_3.png)

## 从数据库导出成hdf5格式文件
rqalpha回测框架目前还只支持数据是hdf5格式，官方提供的hdf5仅包含按天粒度的数据，要支持按分钟回测的话，需求我们自己生成分钟级的hdf5格式数据。  
目前已提供脚本**tools/DumpHDF5.py**来完成这个过程。这个脚本做的事其实就是连接了我们自有的数据库，然后将数据解析成标准的bar格式(time,open,high,low,close,volume等)，再导出成hdf5文件格式。