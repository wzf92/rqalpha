__config__ = {
    #"force_not_open_time": ["14:30-15:00", "22:30-23:00"]
    "force_not_open_time": ["14:31-15:00"]
}


def load_mod():
    from .mod import ForceNotOpen
    return ForceNotOpen()
