import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TravoltCRM.settings')

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack   
import crm_app.routing


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            crm_app.routing.websocket_urlpatterns
        )
    )
})