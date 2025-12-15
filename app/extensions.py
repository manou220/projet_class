"""
Extensions Flask utilisées dans l'application.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_login import LoginManager
from concurrent.futures import ThreadPoolExecutor

# SQLAlchemy utilisé par les modèles optionnels (ex: TestHistory)
db = SQLAlchemy()

# Cache pour améliorer les performances
cache = Cache()

# Flask-Login pour l'authentification
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'  # Protection de session renforcée

# SocketIO est optionnel - peut être désactivé si flask-socketio n'est pas installé
socketio = None
try:
	from flask_socketio import SocketIO
	
	# Detect async library for SocketIO. Prefer `asyncio` (requires `aiohttp`),
	# then fall back to gevent/eventlet if available. The app entrypoint is
	# responsible for any necessary monkey-patching; here we only choose a
	# valid `async_mode` string.
	_async_mode = None
	try:
		import aiohttp  # noqa: F401
		_async_mode = 'asyncio'
	except Exception:
		try:
			import gevent  # noqa: F401
			_async_mode = 'gevent'
		except Exception:
			try:
				import eventlet  # noqa: F401
				_async_mode = 'eventlet'
			except Exception:
				_async_mode = None

	if _async_mode in ('gevent', 'eventlet'):
		# Only explicitly set async_mode for gevent/eventlet which are supported
		# by passing the mode string. For asyncio, let the library autodetect
		# (requires aiohttp/python-socketio async extras) and don't force a mode
		# string which may be rejected by the installed version.
		socketio = SocketIO(cors_allowed_origins='*', async_mode=_async_mode)
	else:
		socketio = SocketIO(cors_allowed_origins='*')
except ImportError:
	# flask-socketio n'est pas installé, socketio reste None
	socketio = None

# Shared thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)
