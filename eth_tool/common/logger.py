import logging
import os
import traceback
import datetime
import time

# Color and style control
style_reset='\033[0m'
style_bold='\033[01m'
style_disable='\033[02m'
# style_reverse='\033[03m'
style_underline='\033[04m'
style_blink='\033[05m'
style_reverse='\033[07m'
style_invisible='\033[08m'
style_strikethrough='\033[09m'

fg_black='\033[30m'
fg_red='\033[31m'
fg_green='\033[32m'
fg_yellow='\033[33m'
fg_blue='\033[34m'
fg_magenta='\033[35m'
fg_cyan='\033[36m'
fg_white='\033[37m'

fg_lightblack='\033[90m'
fg_lightred='\033[91m'
fg_lightgreen='\033[92m'
fg_lightyellow='\033[93m'
fg_lightblue='\033[94m'
fg_lightmagenta='\033[95m'
fg_lightcyan='\033[96m'
fg_lightwhite='\033[97m'

bg_black='\033[40m'
bg_red='\033[41m'
bg_green='\033[42m'
bg_yellow='\033[43m'
bg_blue='\033[44m'
bg_magenta='\033[45m'
bg_cyan='\033[46m'
bg_white='\033[47m'

for color in ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']:
    globals()[color] = lambda s, c=color: globals()['fg_'+c] + s + style_reset
    globals()['light_'+color] = lambda s, c=color: globals()['fg_light'+c] + s + style_reset
    globals()['on_'+color] = lambda s, c=color: globals()['bg_'+c] + s + style_reset

for style in ['reset', 'bold', 'disable', 'underline', 'blink', 'reverse', 'invisible', 'strikethrough']:
    globals()[style] = lambda s, c=style: globals()['style_'+c] + s + style_reset

# Log control
def log(*args, **kwargs):
    kwargs['logging_level'] = logging.INFO
    return __int_log(*args, **kwargs)

def debug(*args, **kwargs):
    kwargs['logging_level'] = logging.debug
    kwargs['color'] = 'blue'
    return __int_log(*args, **kwargs)

def info(*args, **kwargs):
    kwargs['logging_level'] = logging.info
    kwargs['color'] = 'green'
    return __int_log(*args, **kwargs)

def error(*args, **kwargs):
    kwargs['logging_level'] = logging.ERROR
    kwargs['color'] = 'red'
    return __int_log(*args, **kwargs)

def warn(*args, **kwargs):
    kwargs['logging_level'] = logging.WARNING
    kwargs['color'] = 'yellow'
    return __int_log(*args, **kwargs)

def fatal(*args, **kwargs):
    kwargs['logging_level'] = logging.FATAL
    kwargs['color'] = 'on_red'
    return __int_log(*args, **kwargs)

def __int_log(*args, **kwargs):
    logging_level = kwargs.get('logging_level') or logging.INFO
    stacktrace_level = (kwargs.get('stacktrace_level') or 1) + 1

    stacktrace_level = (stacktrace_level * -1) - 1
    stack_line = traceback.extract_stack()[stacktrace_level]
    file_name = os.path.basename(stack_line[0])
    if file_name.endswith('.py'):
        file_name = file_name[0:-3]
    line_number = stack_line[1]
    function_name = stack_line[2]

    length_of_file_and_line = len(file_name) + len(str(line_number))
    time_s = (datetime.datetime.utcnow() - datetime.timedelta(seconds=time.timezone)).strftime("\r%m/%d-%H:%M:%S.%f")[:-2]
    file_s = file_name + ":" + str(line_number)
    global __longest_file_s_len
    try:
        if __longest_file_s_len < len(file_s):
            __longest_file_s_len = len(file_s)
    except NameError:
        __longest_file_s_len = len(file_s)
    file_s = file_s.ljust(__longest_file_s_len)

    color = kwargs.get('color')
    if color is not None:
        args = map(lambda s: globals()[color](str(s)), args)

    strs = [time_s, file_s] + list(args)
    print(*strs)
    return strs
