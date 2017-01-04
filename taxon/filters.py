from math import log10
from decimal import Decimal

import hashlib
import datetime
import ago


def duration(seconds):
    # microseconds
    if seconds > 3600:
        return "{}".format(datetime.timedelta(seconds=seconds))
    if seconds > 60:
        return "{:,.2f} mins".format(seconds / 60.0)
    if seconds <= 1.0e-3:
        return "{:,.4f} us".format(seconds * 1000000.0)
    if seconds <= 1.0:
        return "{:,.4f} ms".format(seconds * 1000.0)
    return "{:,.4f} sec".format(seconds)


def humana_date(*args, **kwargs):
    return ago.human(*args, **kwargs)


def md5(dat):
    return hashlib.md5(dat.encode('utf8')).hexdigest()


def human_date_utc(*args, **kwargs):
    if isinstance(args[0], (int, float, str)):
        args = [datetime.datetime.utcfromtimestamp(float(args[0]))] + list(args[1:])
    delta = (datetime.datetime.utcnow() - args[0])
    delta = delta - datetime.timedelta(microseconds=delta.microseconds)
    result = ago.human(delta, *args[1:], **kwargs)
    return "just now" if result == " ago" else result


def comma(value):
    if isinstance(value, (float, Decimal)):
        return "{:,.2f}".format(value)
    elif isinstance(value, int):
        return "{:,}".format(value)
    else:
        return "NaN"
