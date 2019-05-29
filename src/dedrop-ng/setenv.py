#!/usr/bin/env python3

# Source: https://github.com/anvilventures/lookinsidethebox/blob/master/setenv.py


from hashlib import md5
import sys
import time

if sys.version_info[0] < 3:
    raise Exception("This module is Python 3 only")


def output_env(name, value):
    print("%s=%s; export %s" % (name, value, name))


def is_valid_time_limited_cookie(cookie):
    try:
        t_when = int(cookie[:8], 16) ^ 1686035233
        if abs(time.time() - t_when) < 86400 * 2 and \
                md5(cookie[:8].encode("utf-8?") + b'traceme').hexdigest()[:6] \
                == cookie[8:]:
            return True
    except Exception:
        pass
    return False


def generate_time_cookie():
    t = int(time.time())
    c = 1686035233
    s = "%.8x" % (t ^ c)
    h = md5(s.encode("utf-8?") + b"traceme").hexdigest()
    ret = "%s%s" % (s, h[:6])
    if not is_valid_time_limited_cookie(ret):
        raise Exception("error in generating cookie")
    return ret


c = generate_time_cookie()
output_env("DBDEV", c)
# output_env("DBDEV", "ANVILVENTURES")
# output_env("DBDEV_AUTOMATION", "1")
# output_env("DBTRACEFILE", "/tmp/dropbox_trace_file")
