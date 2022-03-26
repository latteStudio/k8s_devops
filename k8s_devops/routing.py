from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from django.urls import re_path
from django.conf.urls import url
from k8s_devops.consumers import StreamConsumer

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            re_path(r'^workload/pod_terminal/(?P<namespace>.*)/(?P<pod_name>.*)/(?P<container>.*)', StreamConsumer),
        ])
    ),
})
