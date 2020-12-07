__config__ = {
    "slice": 240,
    "size": 2000,
}

def load_mod():
    from .mod import CalcFlowFactor
    return CalcFlowFactor()
