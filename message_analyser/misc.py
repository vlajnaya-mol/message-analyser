import time
import logging

delay = 0.05
months_border = 2 # if the conversation is shorter than this values than xticks will be weeks, not months.


def avg(l):
    if not l:
        return 0
    return sum(l) / len(l)


def log_line(*args):
    logging.getLogger("message_analyser").log(logging.INFO, ' '.join([str(arg) for arg in args]) + '\n')


def time_offset(date):
    return (time.timezone if (time.localtime(int(time.mktime(date.timetuple()))).tm_isdst == 0)
            else time.altzone) / 60 / 60 * -1
