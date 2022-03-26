from django.urls import re_path
from . import views
app_name = 'storage'

urlpatterns = [
    re_path('^configmaps$', views.configmaps, name='configmaps'),
re_path('^pvcs$', views.pvcs, name='pvcs'),
re_path('^secrets$', views.secrets, name='secrets'),

    re_path('^configmaps_api$', views.configmaps_api, name='configmaps_api'),
re_path('^pvcs_api$', views.pvcs_api, name='pvcs_api'),
re_path('^secrets_api$', views.secrets_api, name='secrets_api'),

]