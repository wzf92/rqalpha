__config__ = {
    "slice": 14
}

def load_mod():
    from .mod import CalcRsiFactor
    return CalcRsiFactor()
