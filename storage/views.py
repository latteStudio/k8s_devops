from django.shortcuts import render

# Create your views here.
from django.http import QueryDict, JsonResponse
from k8s_devops import k8s
from kubernetes import client, config



def configmaps(request):
    return render(request, 'storage/configmaps.html')


def configmaps_api(request):
    code = 0
    msg = ""
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()
    if request.method == "GET":
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for cm in core_api.list_namespaced_config_map(namespace=namespace).items:
                name = cm.metadata.name
                namespace = cm.metadata.namespace
                data_length = ("0" if cm.data is None else len(cm.data))
                create_time = cm.metadata.creation_timestamp

                cm = {"name": name, "namespace": namespace, "data_length": data_length, "create_time": create_time}
                # 根据搜索值返回数据
                if search_key:
                    if search_key in name:
                        data.append(cm)
                else:
                    data.append(cm)
                code = 0
                msg = "获取数据成功"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限"
            else:
                msg = "获取数据失败"
        count = len(data)

        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit'))
        start = (page - 1) * limit
        end = page * limit
        data = data[start:end]

        res = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(res)
    elif request.method == "DELETE":
        request_data = QueryDict(request.body)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        try:
            core_api.delete_namespaced_config_map(namespace=namespace, name=name)
            code = 0
            msg = "删除成功."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有删除权限"
            else:
                msg = "删除失败！"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)


def pvcs(request):
    return render(request, 'storage/pvcs.html')


def pvcs_api(request):
    code = 0
    msg = ""
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()
    if request.method == "GET":
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for pvc in core_api.list_namespaced_persistent_volume_claim(namespace=namespace).items:
                name = pvc.metadata.name
                namespace = pvc.metadata.namespace
                labels = pvc.metadata.labels
                storage_class_name = pvc.spec.storage_class_name
                access_modes = pvc.spec.access_modes
                capacity = (pvc.status.capacity if pvc.status.capacity is None else pvc.status.capacity["storage"])
                volume_name = pvc.spec.volume_name
                status = pvc.status.phase
                create_time = pvc.metadata.creation_timestamp

                pvc = {"name": name, "namespace": namespace, "lables": labels,
                       "storage_class_name": storage_class_name, "access_modes": access_modes, "capacity": capacity,
                       "volume_name": volume_name, "status": status, "create_time": create_time}
                # 根据搜索值返回数据
                if search_key:
                    if search_key in name:
                        data.append(pvc)
                else:
                    data.append(pvc)
                code = 0
                msg = "获取数据成功"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限"
            else:
                msg = "获取数据失败"
        count = len(data)

        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit'))
        start = (page - 1) * limit
        end = page * limit
        data = data[start:end]

        res = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(res)

    elif request.method == "DELETE":
        request_data = QueryDict(request.body)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        try:
            core_api.delete_namespaced_service(namespace=namespace, name=name)
            code = 0
            msg = "删除成功."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有删除权限"
            else:
                msg = "删除失败！"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)


def secrets(request):
    return render(request, 'storage/secrets.html')


def secrets_api(request):
    code = 0
    msg = ""
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    if request.method == "GET":
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for secret in core_api.list_namespaced_secret(namespace=namespace).items:
                name = secret.metadata.name
                namespace = secret.metadata.namespace
                data_length = ("空" if secret.data is None else len(secret.data))
                create_time = secret.metadata.creation_timestamp

                se = {"name": name, "namespace": namespace, "data_length": data_length, "create_time": create_time}
                # 根据搜索值返回数据
                if search_key:
                    if search_key in name:
                        data.append(se)
                else:
                    data.append(se)
                code = 0
                msg = "获取数据成功"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限"
            else:
                msg = "获取数据失败"
        count = len(data)

        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit'))
        start = (page - 1) * limit
        end = page * limit
        data = data[start:end]

        res = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(res)

    elif request.method == "DELETE":
        request_data = QueryDict(request.body)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        try:
            core_api.delete_namespaced_secret(namespace=namespace, name=name)
            code = 0
            msg = "删除成功."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有删除权限"
            else:
                msg = "删除失败！"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)