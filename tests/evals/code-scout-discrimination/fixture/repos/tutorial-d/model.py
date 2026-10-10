# Self-authored synthetic fixture; never fetched from a third party.
def rate(snr):
    import math
    return math.log2(1 + snr)
