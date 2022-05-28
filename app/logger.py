# import colorlog
from colorlog import ColoredFormatter, StreamHandler, getLogger

formatter = ColoredFormatter(
	'%(log_color)s%(levelname)s%(reset)s:%(asctime)s:%(purple)s%(name)s%(reset)s:%(log_color)s%(message)s%(reset)s',
	datefmt=None,
	reset=True,
	log_colors={
		'DEBUG':    'cyan',
		'INFO':     'green',
		'WARNING':  'yellow',
		'ERROR':    'red',
		'CRITICAL': 'red,bg_white',
	},
	secondary_log_colors={},
	style='%'
)
handler = StreamHandler()
handler.setFormatter(formatter)
logger = getLogger('ergopad')
logger.addHandler(handler)

# prevent logging from other handlers
import logging
logging.getLogger('uvicorn.error').propagate = False
logging.getLogger('sqlalchemy.engine.Engine').propagate = False
logging.getLogger('sqlalchemy.pool.impl.QueuePool').propagate = False
logging.getLogger('ergopad').propagate = False

import inspect
myself = lambda: inspect.stack()[1][3]
