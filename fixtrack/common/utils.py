import os


def expand_path(p):
    return os.path.abspath(os.path.expanduser(p))
