DEFAULT_TIMEOUT = 0.2


def resolveTimeout(specified):
    if specified is None:
        return DEFAULT_TIMEOUT
    return specified
