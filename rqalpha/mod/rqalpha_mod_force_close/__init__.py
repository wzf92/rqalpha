__config__ = {
    "force_close_time": ["14:55-15:00", "22:55-23:00"]
}


def load_mod():
    from .mod import ForceClose
    return ForceClose()
