import requests

DEBUG = True

#region LOGGING
import logging
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"
COLORS = {'WARNING': YELLOW, 'INFO': WHITE, 'DEBUG': BLUE, 'CRITICAL': YELLOW, 'ERROR': RED}
# logging.basicConfig(format=f"[%(asctime)s] %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%m-%d %H:%M', level=logging.DEBUG)
def formatter_message(message, use_color = True):
    if use_color: message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else: message = message.replace("$RESET", "").replace("$BOLD", "")
    return message
class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color = True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)
        
class ColoredLogger(logging.Logger):
    FORMAT = "[$BOLD%(name)-20s$RESET][%(levelname)-18s]  %(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
    COLOR_FORMAT = formatter_message(FORMAT, True)
    def __init__(self, name):
        logging.Logger.__init__(self, name, (logging.INFO, logging.DEBUG)[DEBUG])

        color_formatter = ColoredFormatter(self.COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)
        return

logging.setLoggerClass(ColoredLogger)        
#endregion LOGGING

###
if __name__ == '__main__':
    print(f'test logging...')
    logging.debug('debug')       # 10 
    logging.info('info')         # 20
    logging.warning('warning')   # 30 - warn deprecated
    logging.error('error')       # 40
    logging.critical('critical') # 50
