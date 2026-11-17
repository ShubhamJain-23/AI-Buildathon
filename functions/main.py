import sys
import os

# Ensure local functions directory is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

from firebase_functions import https_fn
from werkzeug.wrappers import Response
from a2wsgi import ASGIMiddleware
from ap_agent.api import app

wsgi_app = ASGIMiddleware(app)

@https_fn.on_request(memory=512, timeout_sec=120)
def api(req: https_fn.Request) -> https_fn.Response:
    """Entry point for Firebase Functions v2 routing all requests to FastAPI."""
    return Response.from_app(wsgi_app, req.environ)
