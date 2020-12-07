from rqalpha import run_file
import pymongo

init_config = {
  "base": {
    "start_date": "2015-01-01",
    "end_date": "2020-12-01",
    "frequency": "1m",
    "accounts": {
        "future": 1000000
    }
  },
  "mod": {
    "sys_progress": {
      "enabled": True,
      "show": True
    },
    "sys_analyser": {
      "enabled": True,
      "report_save_path": "report",
      "plot": True
    }
  },
  "strategy": {
      "flow_through":
      {
          "contract": "I88",
          "open_long_threshold": "> 0.1",
          "close_long_threshold": "< 0.1",
          "open_short_threshold": "< -0.1",
          "close_short_threshold": "> -0.1",
      }
  }
}

strategy_file_path = "/Users/zhifeng/Projects/rqalpha/rqalpha/examples/strategy_flow.py"

host = "121.40.85.7"
port = 9999
server_addr = "mongodb://%s:%d/" % (host, port)
client = pymongo.MongoClient(server_addr)

# exit(0)
for i in range(1, 10):
    for j in range(1, 10):
        print("%d %d" % (i, j))
        olt = "> %.1f" % (float(i) / 10)
        ost = "< -%.1f" % (float(i) / 10)
        clt = "< %.1f" % (float(j) / 10)
        cst = "> -%.1f" % (float(j) / 10)
        config = init_config
        config["strategy"]["flow_through"]["open_long_threshold"] = olt
        config["strategy"]["flow_through"]["open_short_threshold"] = ost
        config["strategy"]["flow_through"]["close_long_threshold"] = clt
        config["strategy"]["flow_through"]["close_short_threshold"] = cst
        res = run_file(strategy_file_path, config)

        info = res["sys_analyser"]["summary"]
        info["open_long_threshold"] = olt
        info["open_short_threshold"] = ost
        info["close_long_threshold"] = clt
        info["close_short_threshold"] = cst
        print(info)
        exit(0)
        client["backtrace_report_flow_through"]["I88"].insert(info)