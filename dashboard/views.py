from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, QueryDict

from kubernetes import client, config
import random
import hashlib
import os
from k8s_devops import k8s # 包含公共功能函数、装饰器的模块
from dashboard import node_data

def login(request):
    """
    实现登陆认证，
    有Token和kubeconfig两种，本身都是借助k8s-client库向api-server发起请求认证，这里代码只是中转；
    从request的POST对象中取出代表认证方式的字符串，如Token和kubeconfig，然后分别进行不同的处理，即调用不用的认证方式向k8s的api-server \
        发起请求，
    认证成功，跳转到首页，否则提示到前端，认证失败的原因

    接收get和post请求
    get请求，返回login.html
    当操作了login.html相关按钮，触发事件，发起ajax请求到后端，携带相关数据，然后由login处理
    前端定义了token和file分别携带客户端的token和kubeconfig文件对象数据，
    然后接收login函数处理后的数据，分别对成功、错误进行展示
    :param request:
    :return:
    """
    if request.method == 'GET': # get方法，下载展示到登陆页面
        return render(request, 'login.html')
    if request.method == 'POST':
        token = request.POST.get("token", None)
        if token:
            # token认证
            if k8s.auth_check('token', token):
                code = 0
                msg = 'token认证成功'
                request.session['is_login'] = True
                request.session['auth_type'] = 'token'
                request.session['token'] = token
            else:
                code = 1
                msg = 'token无效'
        else:
            # kubeconfig认证
            file_obj = request.FILES.get("file")
            random_filename = hashlib.md5(str(random.random()).encode()).hexdigest()
            file_path = os.path.join('kubeconfig', random_filename)
            print(file_path)
            try:
                with open(file_path, 'w', encoding='utf8') as f:
                    data = file_obj.read().decode()  # bytes转str
                    f.write(data)
            except Exception:
                code = 1
                msg = "kubeconfig文件类型错误！"
            if k8s.auth_check('kubeconfig', file_path):
                code = 0
                msg = 'kubeconfig认证成功'
                request.session['is_login'] = True
                request.session['auth_type'] = 'kubeconfig'
                request.session['token'] = file_path
            else:
                code = 1
                msg = 'kubeconfig无效'
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)


def node_resource(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    res = node_data.node_resource(core_api)
    return JsonResponse(res)


@k8s.login_is_required  # index = login_is_required(index)
def index(request):
    """
    检查是否登陆，是则展示首页，否则就跳转到登陆页面
    :param request:
    :return:
    """
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    node_resouces = node_data.node_resource(core_api)
    # 是个字典

    # 存储资源
    pv_list = []
    for pv in core_api.list_persistent_volume().items:
        pv_name = pv.metadata.name
        capacity = pv.spec.capacity["storage"]  # 返回字典对象
        access_modes = pv.spec.access_modes
        reclaim_policy = pv.spec.persistent_volume_reclaim_policy
        status = pv.status.phase
        if pv.spec.claim_ref is not None:
            pvc_ns = pv.spec.claim_ref.namespace
            pvc_name = pv.spec.claim_ref.name
            claim = "%s/%s" % (pvc_ns, pvc_name)
        else:
            claim = "未关联PVC"
        storage_class = pv.spec.storage_class_name
        create_time = k8s.dt_format(pv.metadata.creation_timestamp)

        data = {"pv_name": pv_name, "capacity": capacity, "access_modes": access_modes,
                "reclaim_policy": reclaim_policy, "status": status,
                "claim": claim, "storage_class": storage_class, "create_time": create_time}
        pv_list.append(data)


    return render(request, 'index.html', {'pv_list': pv_list, 'node_resouces': node_resouces})


def logout(request):
    request.session.clear()
    request.session.flush()
    return redirect(login)

from django.views.decorators.clickjacking import xframe_options_exempt
@xframe_options_exempt
def ace_editor(request):
    resource_type = request.GET.get('resource')
    ns_name = request.GET.get('namespace')
    name = request.GET.get('name')

    data = {'resource': resource_type, 'namespace': ns_name, 'name': name}

    return render(request, 'ace_editor.html', context={'data': data})


def export_resource_yaml(request):
    # 先认证
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    k8s.load_auth_config(auth_type, token)

    # 后实例化，可以请求不同k8s资源的api实例
    core_api = client.CoreV1Api()  # namespace,pod,service,pv,pvc
    apps_api = client.AppsV1Api()  # deployment
    networking_api = client.NetworkingV1beta1Api()  # ingress
    storage_api = client.StorageV1Api()  # storage_class

    ns_name = request.GET.get('namespace')
    resource = request.GET.get('resource')
    name = request.GET.get('name')

    code = 0
    msg = ""
    res = {}
    result = None

    import yaml, json
    if resource == "namespace":
        try:
            # 坑，不要写py测试，print会二次处理影响结果，到时测试不通
            result = core_api.read_namespace(name=name, _preload_content=False).read()
            result = str(result, "utf-8")  # bytes转字符串
            result = yaml.safe_dump(json.loads(result))  # str/dict -> json -> yaml
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'node':
        try:
            result = core_api.read_node(name=name, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "pv":
        try:
            result = core_api.read_persistent_volume(name=name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'deployment':
        try:
            result = apps_api.read_namespaced_deployment(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'replicaset':
        try:
            result = apps_api.read_namespaced_replica_set(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'daemonset':
        try:
            result = apps_api.read_namespaced_daemon_set(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'statefulset':
        try:
            result = apps_api.read_namespaced_stateful_set(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'pod':
        try:
            result = core_api.read_namespaced_pod(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'service':
        try:
            result = core_api.read_namespaced_service(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'ingress':
        try:
            result = networking_api.read_namespaced_ingress(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'pvc':
        try:
            result = core_api.read_namespaced_persistent_volume_claim(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e

    elif resource == 'configmap':
        try:
            result = core_api.read_namespaced_config_map(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'secret':
        try:
            result = core_api.read_namespaced_secret(name=name, namespace=ns_name, _preload_content=False).read()
            result = str(result, 'utf-8')
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    #     elif resource == "pv":
    #         try:
    #             result = core_api.read_persistent_volume(name=name, _preload_content=False).read()
    #             result = str(result, "utf-8")
    #             result = yaml.safe_dump(json.loads(result))
    #         except Exception as e:
    #             code = 1
    #             msg = e

    print(res)
    res = {'code': code, 'msg': msg, 'data': result}
    return JsonResponse(res)


