from django.shortcuts import render

# Create your views here.
from k8s_devops import k8s
from django.http import QueryDict, JsonResponse
from kubernetes import client, config


def ingresses(request):
    return render(request, 'loadbalancer/ingresses.html')


def ingresses_api(request):
    code = 0
    msg = ""
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    networking_api = client.NetworkingV1beta1Api()
    if request.method == "GET":
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for ing in networking_api.list_namespaced_ingress(namespace=namespace).items:
                name = ing.metadata.name
                namespace = ing.metadata.namespace
                labels = ing.metadata.labels
                service = "None"
                http_hosts = "None"
                for h in ing.spec.rules:
                    host = h.host
                    path = ("/" if h.http.paths[0].path is None else h.http.paths[0].path)
                    service_name = h.http.paths[0].backend.service_name
                    service_port = h.http.paths[0].backend.service_port
                    http_hosts = {'host': host, 'path': path, 'service_name': service_name,
                                  'service_port': service_port}

                https_hosts = "None"
                if ing.spec.tls is None:
                    https_hosts = ing.spec.tls
                else:
                    for tls in ing.spec.tls:
                        host = tls.hosts[0]
                        secret_name = tls.secret_name
                        https_hosts = {'host': host, 'secret_name': secret_name}

                create_time = ing.metadata.creation_timestamp

                ing = {"name": name, "namespace": namespace, "labels": labels, "http_hosts": http_hosts,
                       "https_hosts": https_hosts, "service": service, "create_time": create_time}
                # ???????????????????????????
                if search_key:
                    if search_key in name:
                        data.append(ing)
                else:
                    data.append(ing)
                code = 0
                msg = "??????????????????"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "??????????????????"
            else:
                msg = "??????????????????"
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
            networking_api.delete_namespaced_ingress(namespace=namespace, name=name)
            code = 0
            msg = "????????????."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "??????????????????"
            else:
                msg = "???????????????"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)


def services(request):
    return render(request, 'loadbalancer/services.html')


def services_api(request):
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
            for svc in core_api.list_namespaced_service(namespace=namespace).items:
                name = svc.metadata.name
                namespace = svc.metadata.namespace
                labels = svc.metadata.labels
                type = svc.spec.type
                cluster_ip = svc.spec.cluster_ip
                ports = []
                for p in svc.spec.ports:  # ?????????????????????????????????
                    port_name = p.name
                    port = p.port
                    target_port = p.target_port
                    protocol = p.protocol
                    node_port = ""
                    if type == "NodePort":
                        node_port = " <br> NodePort: %s" % p.node_port

                    port = {'port_name': port_name, 'port': port, 'protocol': protocol, 'target_port': target_port,
                            'node_port': node_port}
                    ports.append(port)

                selector = svc.spec.selector
                create_time = svc.metadata.creation_timestamp

                # ??????????????????Pod
                endpoint = ""
                for ep in core_api.list_namespaced_endpoints(namespace=namespace).items:
                    if ep.metadata.name == name and ep.subsets is None:
                        endpoint = "?????????"
                    else:
                        endpoint = "?????????"

                svc = {"name": name, "namespace": namespace, "type": type,
                       "cluster_ip": cluster_ip, "ports": ports, "labels": labels,
                       "selector": selector, "endpoint": endpoint, "create_time": create_time}
                # ???????????????????????????
                if search_key:
                    if search_key in name:
                        data.append(svc)
                else:
                    data.append(svc)
                code = 0
                msg = "??????????????????"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "??????????????????"
            else:
                msg = "??????????????????"
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
            msg = "????????????."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "??????????????????"
            else:
                msg = "???????????????"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)