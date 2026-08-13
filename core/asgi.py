"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
import api.routing

class DebugMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            print("WS REQUEST SCOPE:", scope)
        try:
            return await self.inner(scope, receive, send)
        except Exception as e:
            print("WS REQUEST EXCEPTION:", e)
            raise

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": DebugMiddleware(URLRouter(
        api.routing.websocket_urlpatterns
    )),
})
