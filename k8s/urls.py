from django.urls import path, re_path, include
from k8s import views

urlpatterns = [
    re_path('^node_details_pod_list', views.node_details_pod_list, name='node_details_pod_list'),
    re_path('^nodes/$', views.nodes, name='nodes'),
    re_path('^nodes_api/$', views.nodes_api, name='nodes_api'),
    re_path('^node_details', views.node_details, name='node_details'),

    re_path('^namespaces/$', views.namespaces, name='namespaces'),
    re_path('^namespaces_api/$', views.namespaces_api, name='namespaces_api'),



    re_path('^pvs/$', views.pvs, name='pvs'),
    re_path('^pvs_api/$', views.pvs_api, name='pvs_api'),
    re_path('^pvs_create/$', views.pvs_create, name='pvs_create'),


]
app_name = 'k8s'
# urlpatterns = [
#     # path('admin/', admin.site.urls),
#     re_path('^node/$', views.node, name="node"),
#     re_path('^node_api/$', views.node_api, name="node_api"),
#     re_path('^node_details/$', views.node_details, name="node_details"),
#     re_path('^node_details_pod_list/$', views.node_details_pod_list, name="node_details_pod_list"),
#     re_path('^pv/$', views.pv, name="pv"),
#     re_path('^pv_create/$', views.pv_create, name="pv_create"),
#     re_path('^pv_api/$', views.pv_api, name="pv_api"),
# ]
