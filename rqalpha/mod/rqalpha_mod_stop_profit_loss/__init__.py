__config__ = {
    "stop_profit": 0.01,
    "stop_loss": 0.01,
}


def load_mod():
    from .mod import StopProfitLoss
    return StopProfitLoss()
