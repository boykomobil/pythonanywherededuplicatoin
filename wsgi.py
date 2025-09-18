import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from src.app import app as application  # WSGI entrypoint
