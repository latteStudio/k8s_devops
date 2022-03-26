import os
from kubernetes import client, config
from django.shortcuts import redirect

def login_is_required(func):
    def wrapper(request, *args, **kwargs):
        is_login = request.session.get('is_login', False)
        if is_login:
            return func(request, *args, **kwargs)
        else:
            return redirect('login')
    return wrapper

def auth_check(method, content):
    if method == 'token':
        token = content
        configuration = client.Configuration()
        configuration.host = "https://192.168.80.100:6443"  # APISERVER地址
        configuration.ssl_ca_cert = os.path.join('kubeconfig', 'ca.crt') # CA证书
        configuration.verify_ssl = True  # 启用证书验证

        configuration.api_key = {"authorization": "Bearer " + token}  # 指定Token字符串
        client.Configuration.set_default(configuration)

        try:
            core_api = client.CoreApi()
            core_api.get_api_versions()
            return True
        except Exception as e:
            print(e)
            return False
    if method == 'kubeconfig':
        # kube_config_file_name = content
        kube_config_file_path = content

        config.load_kube_config(r"%s" % kube_config_file_path)

        try:
            core_api = client.CoreApi()
            core_api.get_api_versions()
            return True
        except Exception as e:
            print(e)
            return False


def load_auth_config(method, content):
    if method == 'token':
        token = content
        configuration = client.Configuration()
        configuration.host = "https://192.168.80.100:6443"  # APISERVER地址
        configuration.ssl_ca_cert = os.path.join('kubeconfig', 'ca.crt') # CA证书
        configuration.verify_ssl = True  # 启用证书验证

        configuration.api_key = {"authorization": "Bearer " + token}  # 指定Token字符串
        client.Configuration.set_default(configuration)

    if method == 'kubeconfig':
        kube_config_file_path = content

        config.load_kube_config(r"%s" % kube_config_file_path)


# 时间格式化
from datetime import date,timedelta
def dt_format(timestamp):
    t = date.strftime((timestamp + timedelta(hours=8)), '%Y-%m-%d %H:%M:%S')
    return t