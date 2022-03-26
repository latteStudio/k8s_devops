from django.urls import re_path
from . import views

app_name = 'loadbalancer'

urlpatterns = [
    re_path('^ingresses$', views.ingresses, name='ingresses'),
    re_path('^ingresses_api$', views.ingresses_api, name='ingresses_api'),
    re_path('^services$', views.services, name='services'),
    re_path('^services_api$', views.services_api, name='services_api'),

]