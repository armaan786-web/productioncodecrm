from . import consumers
from django.urls import path, re_path
websocket_urlpatterns = [
    path("ws/chat/<str:group_id>/", consumers.ChatConsumer.as_asgi()),
]
