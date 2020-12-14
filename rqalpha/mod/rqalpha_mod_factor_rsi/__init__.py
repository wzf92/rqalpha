__config__ = {
    "slice": 14,
    "log_dir": "report"
}

def load_mod():
    from .mod import CalcRsiFactor
    print('right')
    return CalcRsiFactor()
