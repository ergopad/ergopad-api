import logging 
from colorlog import ColoredFormatter, StreamHandler, getLogger

LEIF = 5
logging.addLevelName(LEIF, 'LEIF')
formatter = ColoredFormatter(
    # {color}, fg_{color}, bg_{color}: Foreground and background colors.
    # bold, bold_{color}, fg_bold_{color}, bg_bold_{color}: Bold/bright colors.
    # thin, thin_{color}, fg_thin_{color}: Thin colors (terminal dependent).
    # reset: Clear all formatting (both foreground and background colors).
	'%(log_color)s%(levelname)s%(reset)s:%(asctime)s:%(purple)s%(name)s%(reset)s:%(log_color)s%(message)s%(reset)s',
	datefmt=None,
	reset=True,
    # black, red, green, yellow, blue, purple, cyan, white
	log_colors={
		'DEBUG':    'cyan',
		'INFO':     'green',
		'WARNING':  'yellow',
		'ERROR':    'red',
		'CRITICAL': 'red,bg_white',
        'LEIF':     'white,bg_green'
	},
	secondary_log_colors={},
	style='%'
)
handler = StreamHandler()
handler.setFormatter(formatter)
logger = getLogger('ergopad')
logger.setLevel('LEIF')
logger.addHandler(handler)

# prevent logging from other handlers
import logging
logging.getLogger('uvicorn.error').propagate = False
logging.getLogger('sqlalchemy.engine.Engine').propagate = False
logging.getLogger('sqlalchemy.pool.impl.QueuePool').propagate = False
logging.getLogger('ergopad').propagate = False

import inspect
myself = lambda: inspect.stack()[1][3]
