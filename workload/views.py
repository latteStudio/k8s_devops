from django.shortcuts import render

# Create your views here.
from k8s_devops.k8s import login_is_required, load_auth_config, dt_format
from kubernetes import client, config
from django.http import JsonResponse
from django.http import QueryDict   # 对body进行封装成字典，可以用get方法，根据key取得对应的value

@login_is_required
def deployments(request):
    return render(request, 'workload/deployments.html')

@login_is_required
def deployments_api(request):
    code = 0
    msg = ""
    count = 0
    data = []

    auth_type = request.session.get('auth_type')
    token = request.session.get('token')

    load_auth_config(auth_type, token)

    appsv1_api = client.AppsV1Api()

    method = request.method
    ns_name = request.GET.get('namespace')


    if method == 'GET':
        search_key = request.GET.get('search_key')
        for dp in appsv1_api.list_namespaced_deployment(ns_name).items:
            name = dp.metadata.name
            namespace = dp.metadata.namespace
            replicas = dp.spec.replicas
            avaliable_replicas = (0 if dp.status.available_replicas is None else dp.status.available_replicas)
            labels = dp.metadata.labels
            selector = dp.spec.selector.match_labels
            if len(dp.spec.template.spec.containers) > 1:
                image = ""
                n = 1
                for c in dp.spec.template.spec.containers:
                    status = "运行中" if dp.status.conditions[0].status == "True" else "异常"
                    image = c.image
                    image += "[%s]: %s / %s" % (n, image, status)
                    image += "<br>"
                    n + 1
            else:
                status = "运行中" if dp.status.conditions[0].status == "True" else "异常"
                image = dp.spec.template.spec.containers[0].image
                images = "%s / %s" %(image, status)

            create_time = dp.metadata.creation_timestamp
            dp = {'name': name, "namespace": namespace, 'replicas': replicas,
                  'available_replicas': avaliable_replicas, 'labels': labels, 'selector': selector,
                  'images': images, 'create_time': create_time
                  }

            if search_key:
                if search_key in name:
                    data.append(dp)

            else:
                data.append(dp)
            msg = "dp查询成功"

        count = len(data)
        res = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(res)
    elif method == 'DELETE':
        req_data = QueryDict(request.body)
        dp_name = req_data.get('name')
        ns_name = req_data.get('namespace')
        try:
            appsv1_api.delete_namespaced_deployment(name=dp_name, namespace=ns_name)
            msg = '删除成功'
        except Exception as e:
            code = 1
            msg = '删除异常'
        res = {'code': code, 'msg': msg}
        print(res)
        return JsonResponse(res)
    elif method == 'PUT':
        req_data = QueryDict(request.body)
        dp_name = req_data.get('name')
        ns_name = req_data.get('namespace')
        replicas = int(req_data.get('replicas'))

        try:
            # 根据ns和name，获得dp的具体实例，然后通过spec.replicas属性，获取当然副本数，
            # 同时设置上下限的副本区间，不在此区间，就失败，在此区间，大于当前副本就是扩容，否则就是缩容
            body = appsv1_api.read_namespaced_deployment(name=dp_name, namespace=ns_name)
            # print(body)
            current_replicas = body.spec.replicas

            min_replicas = 0
            max_replicas = 20
            if replicas <= min_replicas or replicas > max_replicas:
                code = 1
                msg = "扩所容区间在0（不包含）~20之间，请重新选择，副本数不可为0，大于20需管理员身份添加"
            elif replicas > current_replicas:

                # 方式1 可以
                # 反思：
                """
                1、基础不好，比如http要熟，k8s熟，就好很多，底层懂越多越好，以后会学的很快，不然上层api封装太多，一个错就Google半天！还没用，遇到一个，搜一次？太傻b
                2、英语能力，看官网文档，github 的commit，耐心看，立刻试试，一个不行再换下一个，而不是一直搜，（不试试怎么直到，以解决问题以首要！）
                3、会google、英文、官网文档，还要匹配对应版本，不同版本api可能差异很大，（学会自己看源码，分析报错）
                """
                body = [{"op": "replace", "path": "/spec/replicas", "value": replicas}]
                appsv1_api.patch_namespaced_deployment(name=dp_name, namespace=ns_name, body=body)

                # 方式2 不行
                # body.spec.replicas = replicas
                # appsv1_api.patch_namespaced_deployment(dp_name, ns_name, {'replicas': replicas})
                msg = '扩容成功'

            elif replicas < current_replicas:
                body = [{"op": "replace", "path": "/spec/replicas", "value": replicas}]
                appsv1_api.patch_namespaced_deployment(dp_name, ns_name, body=body)
                # body.spec.replicas = replicas
                # appsv1_api.patch_namespaced_deployment(dp_name, ns_name, {'replicas': replicas})
                msg = '缩容成功'
            elif replicas == current_replicas:
                code = 1
                msg = '无需扩所容'
        except Exception as e:
            print(e)
            code = 1
            status = getattr(e, 'status')
            if status == '403':
                msg = '权限不足'
            else:
                msg = '扩缩容失败'
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

    elif method == 'POST':
        name = request.POST.get("name", None)
        namespace = request.POST.get("namespace", None)
        image = request.POST.get("image", None)
        replicas = int(request.POST.get("replicas", None))
        # 处理标签
        labels = {}
        try:
            for l in request.POST.get("labels", None).split(","):
                k = l.split("=")[0]
                v = l.split("=")[1]
                labels[k] = v
        except Exception as e:
            res = {"code": 1, "msg": "标签格式错误！"}
            return JsonResponse(res)
        resources = request.POST.get("resources", None)
        health_liveness = request.POST.get("health[liveness]",
                                           None)  # {'health[liveness]': ['on'], 'health[readiness]': ['on']}
        health_readiness = request.POST.get("health[readiness]", None)

        if resources == "1c2g":
            resources = client.V1ResourceRequirements(limits={"cpu": "1", "memory": "2Gi"},
                                                      requests={"cpu": "0.9", "memory": "1.9Gi"})
        elif resources == "2c4g":
            resources = client.V1ResourceRequirements(limits={"cpu": "2", "memory": "4Gi"},
                                                      requests={"cpu": "1.9", "memory": "3.9Gi"})
        elif resources == "4c8g":
            resources = client.V1ResourceRequirements(limits={"cpu": "4", "memory": "8Gi"},
                                                      requests={"cpu": "3.9", "memory": "7.9Gi"})
        else:
            resources = client.V1ResourceRequirements(limits={"cpu": "500m", "memory": "1Gi"},
                                                      requests={"cpu": "450m", "memory": "900Mi"})
        liveness_probe = ""
        if health_liveness == "on":
            liveness_probe = client.V1Probe(http_get="/", timeout_seconds=30, initial_delay_seconds=30)
        readiness_probe = ""
        if health_readiness == "on":
            readiness_probe = client.V1Probe(http_get="/", timeout_seconds=30, initial_delay_seconds=30)

        for dp in appsv1_api.list_namespaced_deployment(namespace=namespace).items:
            if name == dp.metadata.name:
                res = {"code": 1, "msg": "Deployment已经存在！"}
                return JsonResponse(res)

        body = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1DeploymentSpec(
                replicas=replicas,
                selector={'matchLabels': labels},
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=labels),
                    spec=client.V1PodSpec(
                        containers=[client.V1Container(
                            # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Container.md
                            name="web",
                            image=image,
                            env=[{"name": "TEST", "value": "123"}, {"name": "DEV", "value": "456"}],
                            ports=[client.V1ContainerPort(container_port=80)],
                            # liveness_probe=liveness_probe,
                            # readiness_probe=readiness_probe,
                            resources=resources,
                        )]
                    )
                ),
            )
        )
        try:
            appsv1_api.create_namespaced_deployment(namespace=namespace, body=body)

            code = 0
            msg = "创建成功."
        except Exception as e:
            print(e)
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限！"
            else:
                msg = "创建失败！"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

@login_is_required
def deployments_create(request):
    return render(request, 'workload/deployments_create.html')


@login_is_required
def deployment_details(request):
    """
    先通过认证，然后取出查询参数的ns_name 和 dp_name 确定是哪个空间下的哪个dp
    实例化3种client_api，用于查询dp管理的replicaset、容器、service ingress等资源！


    :param request:
    :return:
    """
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()
    apps_api = client.AppsV1Api()
    networking_api = client.NetworkingV1beta1Api()

    dp_name = request.GET.get("name")
    namespace = request.GET.get("namespace")

    dp_info = []
    for dp in apps_api.list_namespaced_deployment(namespace=namespace).items:
        if dp_name == dp.metadata.name:
            # dp基本信息：
                # 名称、命名空间、副本数、标签选择器、本身的标签
            name = dp.metadata.name
            namespace = dp.metadata.namespace
            replicas = dp.spec.replicas
            available_replicas = (
                0 if dp.status.available_replicas is None else dp.status.available_replicas)  # ready_replicas
            labels = dp.metadata.labels
            selector = dp.spec.selector.match_labels

            # 通过deployment反查对应service
            service = []
            svc_name = None
            for svc in core_api.list_namespaced_service(namespace=namespace).items:
                if svc.spec.selector == selector:
                    svc_name = svc.metadata.name  # 通过该名称筛选ingress
                    type = svc.spec.type
                    cluster_ip = svc.spec.cluster_ip
                    ports = svc.spec.ports

                    data = {"type": type, "cluster_ip": cluster_ip, "ports": ports}
                    service.append(data)

            # service没有创建，ingress也就没有  ingress->service->deployment->pod
            ingress = {"rules": None, "tls": None}
            for ing in networking_api.list_namespaced_ingress(namespace=namespace).items:
                for r in ing.spec.rules:
                    for b in r.http.paths:
                        if b.backend.service_name == svc_name:
                            ingress["rules"] = ing.spec.rules
                            ingress["tls"] = ing.spec.tls

            # 查出dp关联的所有容器的信息，以列表存储，每个容器都展示有：镜像、健康检查、变量、存储卷等信息
            containers = []
            for c in dp.spec.template.spec.containers:
                c_name = c.name
                image = c.image
                liveness_probe = c.liveness_probe
                readiness_probe = c.readiness_probe
                resources = c.resources  # 在前端处理
                env = c.env
                ports = c.ports
                volume_mounts = c.volume_mounts
                args = c.args
                command = c.command

                container = {"name": c_name, "image": image, "liveness_probe": liveness_probe,
                             "readiness_probe": readiness_probe,
                             "resources": resources, "env": env, "ports": ports,
                             "volume_mounts": volume_mounts, "args": args, "command": command}
                containers.append(container)

            # dp设置的更新策略、容忍度，和存储卷信息
            # 每种存储卷，按类型存储
            tolerations = dp.spec.template.spec.tolerations
            rolling_update = dp.spec.strategy.rolling_update
            volumes = []
            if dp.spec.template.spec.volumes is not None:
                for v in dp.spec.template.spec.volumes:
                    volume = {}
                    if v.config_map is not None:
                        volume["config_map"] = v.config_map
                    elif v.secret is not None:
                        volume["secret"] = v.secret
                    elif v.empty_dir is not None:
                        volume["empty_dir"] = v.empty_dir
                    elif v.host_path is not None:
                        volume["host_path"] = v.host_path
                    elif v.config_map is not None:
                        volume["downward_api"] = v.downward_api
                    elif v.config_map is not None:
                        volume["glusterfs"] = v.glusterfs
                    elif v.cephfs is not None:
                        volume["cephfs"] = v.cephfs
                    elif v.rbd is not None:
                        volume["rbd"] = v.rbd
                    elif v.persistent_volume_claim is not None:
                        volume["persistent_volume_claim"] = v.persistent_volume_claim
                    else:
                        volume["unknown"] = "unknown"
                    volumes.append(volume)

            # dp的历史版本限制上限
            rs_number = dp.spec.revision_history_limit
            create_time = dt_format(dp.metadata.creation_timestamp)



            dp_info = {"name": name, "namespace": namespace, "replicas": replicas,
                       "available_replicas": available_replicas, "labels": labels,
                       "selector": selector, "containers": containers, "rs_number": rs_number,
                       "rolling_update": rolling_update, "create_time": create_time, "volumes": volumes,
                       "tolerations": tolerations, "service": service, "ingress": ingress}
    return  render(request , 'workload/deployments_details.html', {'dp_name':dp_name, 'namespace': namespace, 'dp_info': dp_info})



@login_is_required
def replicaset_api(request):
    """
    get方法，根据，查询参数给的ns_name dp_name 查询dp所关联的所有rs，
        遍历，该ns_name下的所有rs，并根据rs.metadata.owner_referentce[0].name确定其归属dp，
        归属dp和传入的dp_name相等，即为要找到的rs，然后将rs的信息，取出封装，并逐一追加到列表中，最后返回
    post方法，
        根据传入的dp_name ns_name 以及 revision版本，确定要回滚到dp的哪个rs版本
        借助方法：apps_beta_api.create_namespaced_deployment_rollback(name=dp_name, namespace=namespace, body=body)
    :param request:
    :return:
    """
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    load_auth_config(auth_type, token)
    apps_api = client.AppsV1Api()
    apps_beta_api = client.ExtensionsV1beta1Api()

    if request.method == "GET":
        dp_name = request.GET.get("name", None)
        namespace = request.GET.get("namespace", None)
        data = []
        for rs in apps_api.list_namespaced_replica_set(namespace=namespace).items:
            current_dp_name = rs.metadata.owner_references[0].name
            rs_name = rs.metadata.name
            if dp_name == current_dp_name:
                namespace = rs.metadata.namespace
                replicas = rs.status.replicas
                available_replicas = rs.status.available_replicas
                ready_replicas = rs.status.ready_replicas
                revision = rs.metadata.annotations["deployment.kubernetes.io/revision"]
                create_time = dt_format(rs.metadata.creation_timestamp)

                containers = {}
                for c in rs.spec.template.spec.containers:
                    containers[c.name] = c.image

                rs = {"name": rs_name, "namespace": namespace, "replicas": replicas,
                        "available_replicas": available_replicas, "ready_replicas": ready_replicas,
                        "revision":revision, 'containers': containers, "create_time": create_time}
                data.append(rs)
        count = len(data) # 可选，rs默认保存10条，所以不用分页
        res = {"code": 0, "msg": "", "count": count, 'data': data}
        return JsonResponse(res)
    elif request.method == "POST":
        dp_name = request.POST.get("dp_name", None)  # deployment名称
        namespace = request.POST.get("namespace", None)
        revision = request.POST.get("revision", None)
        body = {"name": dp_name, "rollback_to": {"revision": revision}}
        print(body)
        print(dp_name)
        try:
            # clinet 11.0.0 kubernetes 19.6 无法回滚，接口版本匹配
            apps_beta_api.create_namespaced_deployment_rollback(name=dp_name, namespace=namespace, body=body)
            # # apps_api.create_name
            # apps_api.patch_namespaced_deployment(name=dp_name, namespace=namespace, body=body)

            code = 0
            msg = "回滚成功！"
        except Exception as e:
            print(e)
            status = getattr(e, "status")
            if status == 403:
                msg = "你没有回滚权限！"
            else:
                msg = "回滚失败！"
            code = 1
        res = {"code": code, "msg": msg}
        return JsonResponse(res)


def daemonsets(request):
    """
    返回页面；
    列表展示：页面中，数据表格渲染是，请求ds的get接口，得到ds的数据，展示到数据表格中；
    搜索功能：get查询时，根据关键字过滤

    表格行，工具事件，对于yaml，请求ace_editor接口，进而请求yaml展示接口，根据get中查询参数，得到ds的yaml，最终展示
    删除，delete请求，拿到name后，找到并删除
    :param request:
    :return:
    """
    return render(request, 'workload/daemonsets.html')


@login_is_required
def daemonsets_api(request):
    code = 0
    msg = ""
    count = 0
    data = []

    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    print(token)

    load_auth_config(auth_type, token)

    apps_api = client.AppsV1Api()

    if request.method == 'GET':
        try:
            search_key = request.GET.get('search_key', None)
            ns_name = request.GET.get('namespace')
            for ds in apps_api.list_namespaced_daemon_set(namespace=ns_name).items:

                name = ds.metadata.name
                namespace = ds.metadata.namespace
                desired_number = ds.status.desired_number_scheduled
                available_number = ds.status.number_available
                labels = ds.metadata.labels
                selector = ds.spec.selector.match_labels
                containers = {}
                for c in ds.spec.template.spec.containers:
                    containers[c.name] = c.image
                create_time = ds.metadata.creation_timestamp
                ds = {"name": name, "namespace": namespace, "labels": labels, "desired_number": desired_number,
                      "available_number": available_number,
                      "selector": selector, "containers": containers, "create_time": create_time}

                if search_key:
                    if search_key in name:
                        data.append(ds)
                else:
                    data.append(ds)

                msg = '查询成功'
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

    elif request.method == 'DELETE':
        req_data = QueryDict(request.body)
        name = req_data.get('name')
        ns_name = req_data.get('namespace')
        try:
            apps_api.delete_namespaced_daemon_set(namespace=ns_name, name=name)
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

@login_is_required
def statefulsets(request):
    return render(request, 'workload/statefulsets.html')

@login_is_required
def statefulsets_api(request):
    code = 0
    msg = ""
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    load_auth_config(auth_type, token)
    apps_api = client.AppsV1Api()
    if request.method == "GET":
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for sts in apps_api.list_namespaced_stateful_set(namespace).items:
                name = sts.metadata.name
                namespace = sts.metadata.namespace
                labels = sts.metadata.labels
                selector = sts.spec.selector.match_labels
                replicas = sts.spec.replicas
                ready_replicas = ("0" if sts.status.ready_replicas is None else sts.status.ready_replicas)
                # current_replicas = sts.status.current_replicas
                service_name = sts.spec.service_name
                containers = {}
                for c in sts.spec.template.spec.containers:
                    containers[c.name] = c.image
                create_time = sts.metadata.creation_timestamp

                sts = {"name": name, "namespace": namespace, "labels": labels, "replicas": replicas,
                       "ready_replicas": ready_replicas, "service_name": service_name,
                       "selector": selector, "containers": containers, "create_time": create_time}

                # 根据搜索值返回数据
                if search_key:
                    if search_key in name:
                        data.append(sts)
                else:
                    data.append(sts)
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
            apps_api.delete_namespaced_stateful_set(namespace=namespace, name=name)
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


@login_is_required
def pods(request):
    return render(request, 'workload/pods.html')

@login_is_required
def pods_api(request):
    code = 0
    msg = ""
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()
    if request.method == "GET":
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for po in core_api.list_namespaced_pod(namespace).items:
                name = po.metadata.name
                namespace = po.metadata.namespace
                labels = po.metadata.labels
                pod_ip = po.status.pod_ip

                containers = []  # [{},{},{}]
                status = "None"
                # 只为None说明Pod没有创建（不能调度或者正在下载镜像）
                if po.status.container_statuses is None:
                    status = po.status.conditions[-1].reason
                else:
                    for c in po.status.container_statuses:
                        c_name = c.name
                        c_image = c.image

                        # 获取重启次数
                        restart_count = c.restart_count

                        # 获取容器状态
                        c_status = "None"
                        if c.ready is True:
                            c_status = "Running"
                        elif c.ready is False:
                            if c.state.waiting is not None:
                                c_status = c.state.waiting.reason
                            elif c.state.terminated is not None:
                                c_status = c.state.terminated.reason
                            elif c.state.last_state.terminated is not None:
                                c_status = c.last_state.terminated.reason

                        c = {'c_name': c_name, 'c_image': c_image, 'restart_count': restart_count, 'c_status': c_status}
                        containers.append(c)

                create_time = po.metadata.creation_timestamp

                po = {"name": name, "namespace": namespace, "pod_ip": pod_ip,
                      "labels": labels, "containers": containers, "status": status,
                      "create_time": create_time}

                # 根据搜索值返回数据
                if search_key:
                    if search_key in name:
                        data.append(po)
                else:
                    data.append(po)
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
            core_api.delete_namespaced_pod(namespace=namespace, name=name)
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


from django.views.decorators.clickjacking import xframe_options_exempt
# 关闭跨站访问的限制！
@xframe_options_exempt
@login_is_required
def pod_terminal(request):
    """
    返回一个html页面模拟的终端，连接到具体的pod中的容器
    :param request:
    :return:
    """
    namespace = request.GET.get('namespace')
    pod_name = request.GET.get('pod_name')
    containers = request.GET.get('containers').split(',')   # 多个容器名，以, 分割

    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    print(token)    # kubeconfig\bbeb69ea72701ff82b0edb4060905be9 设置的时候，就是这个格式
    token = token.split('\\')[1]

    print('--')
    print(auth_type, token)

    connect = {
        'namespace': namespace,
        'pod_name': pod_name,
        'containers': containers,   # 列表
        'auth_type': auth_type,
        'token': token,
    }
    return render(request, 'workload/terminal.html', {'connect': connect})

@login_is_required
def pod_log(request):
    """
    返回一个html页面，展示最近的pod中的log
    :param request:
    :return:
    """
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    name = request.POST.get('name', None)
    ns_name = request.POST.get('namespace', None)

    # 没有处理pod中多容器情况
    try:
        log_text = core_api.read_namespaced_pod_log(name, ns_name, tail_lines=500)  # 默认500行

        if log_text:
            code = 0
            msg = "获取日志成功"

        else:
            code = 1
            msg = "没有日志"
            log_text = "没有日志"
    except Exception as e:
        status = getattr(e, 'status')
        if status == 403:
            msg = "无查看日志权限"
        else:
            print(e)
            msg = "其他异常"
        code = 1

        log_text = "获取日志异常"
    res = {'code': code, 'msg': msg, 'data': log_text}
    return JsonResponse(res)

