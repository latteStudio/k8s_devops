from django.urls import re_path, path
from workload import views

app_name = 'workload'

urlpatterns = [
    re_path('^deployments$', views.deployments, name = 'deployments'),
    re_path('^deployments_api$', views.deployments_api, name='deployments_api'),
    re_path('^deployments_create$', views.deployments_create, name='deployments_create'),
    re_path('^deployment_details$', views.deployment_details, name='deployment_details'),

    re_path('^replicaset_api', views.replicaset_api, name='replicaset_api'),
    re_path('^daemonsets$', views.daemonsets, name = 'daemonsets'),
    re_path('^daemonsets_api$', views.daemonsets_api, name = 'daemonsets_api'),

    re_path('^statefulsets$', views.statefulsets, name = 'statefulsets'),
    re_path('^statefulsets_api$', views.statefulsets_api, name = 'statefulsets_api'),

    re_path('^pods$', views.pods, name = 'pods'),
    re_path('^pods_api$', views.pods_api, name = 'pods_api'),
    re_path('^pod_log$', views.pod_log, name = 'pod_log'),
    re_path('^pod_terminal$', views.pod_terminal, name = 'pod_terminal'),

]