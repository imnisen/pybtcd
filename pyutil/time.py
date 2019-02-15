import time

Second = 1
Minute = 60 * Second
Hour = 3600 * Second


# Return currerent time as int
def now():
    return int(time.time())
