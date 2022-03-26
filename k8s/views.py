from django.shortcuts import render
from k8s_devops.k8s import load_auth_config, login_is_required # 导入功能函数：是否登陆验证，以及验证函数
# Create your views here.

from kubernetes import config, client
from django.http import JsonResponse
from dashboard import node_data
from k8s_devops import k8s
from django.http import QueryDict   # 包装request的body，成为reqeust_data，从而可以以字典形式，获得delete方法的参数


@login_is_required
def nodes(request):
    """把node详情页分为2个view
    第一个：页面接口——返回框架的html页面，其中页面包含了渲染后的node_api的超链接
    第二个，数据api——返回json格式的数据，填充到上一步返回的html中的layui数据表格中，完成最后的渲染
    """
    return render(request, 'k8s/nodes.html')

@login_is_required
def nodes_api(request):
    """
    1、装饰器，确保请求该view的请求，是已经登陆过的，否则就重定向到登陆页面
    2、登陆后的有token和type2个字段在session中，拿出来，借助load_auth_config函数，对k8s api进行登陆认证
    针对request方法是GET的情况
    3、成功登陆后、得到客户端实例后，请求包含了node信息的api，然后数据封装
        请求过程：
        1、先取出请求中的search_key
        2、查询node api，
            查询成功：然后将得到的数据，追加到data列表中，（如果有search_key）就代表前端发来的是搜索请求，需要in 过滤下，再追加
            查询异常；
                如果有403表示权限不足，如果其他，就是查询异常
        3、最后，检查是否有page，查询参数，如果有代表有分页，根据分页、limit取结果集的切片后，再返回，json格式数据
    :param request:
    :return:
    """
    res = {}
    code = 0
    msg = ""
    data = []  # 存放查询到的node信息，列表格式，前端会遍历
    count = 0
    token = request.session.get('token')
    auth_type = request.session.get('auth_type')
    load_auth_config(auth_type, token)
    core_api = client.CoreV1Api() # 该实例可以查询node资源
    if request.method == "GET":
        # get请求
        search_key = request.GET.get('search_key')
        try:
            # 查询node的api，然后每个node的名称、标签等属性信息，构造成一个node的信息字典
            for node in core_api.list_node_with_http_info()[0].items:
                name = node.metadata.name
                labels = node.metadata.labels
                status = node.status.conditions[-1].status
                scheduler = ("是" if node.spec.unschedulable is None else "否")
                cpu = node.status.capacity['cpu']
                memory = node.status.capacity['memory']
                kebelet_version = node.status.node_info.kubelet_version
                cri_version = node.status.node_info.container_runtime_version
                create_time = node.metadata.creation_timestamp
                node = {"name": name, "labels": labels, "status": status,
                        "scheduler": scheduler, "cpu": cpu, "memory": memory,
                        "kebelet_version": kebelet_version, "cri_version": cri_version,
                        "create_time": create_time}
                if search_key: # 搜索请求
                    if search_key in name:
                        data.append(node)
                else: # 非搜索请求，全量返回
                    data.append(node)

                msg = "查询成功"
                code = 0
                count = len(data)
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                code = 403
                msg = "权限不足"
            else:
                code = 500
                msg = "查询数据失败"

        if request.GET.get('page'): # 如果有分页查询参数
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit'))
            start = (page - 1) * limit
            end = page * limit
            data = data[start:end]

    print(data)
    res = {'code': code, 'msg': msg, 'count': count, 'data': data}
    return JsonResponse(res)


@login_is_required
def node_details(request):
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    print(auth_type)
    print(token)

    node_name = request.GET.get('node_name', None)
    n_r = node_data.node_resource(core_api, node_name)
    n_i = node_data.node_info(core_api, node_name)

    print(n_i)
    print(n_r)
    return render(request, 'k8s/node_details.html', context={"node_name": node_name, "node_resources": n_r, "node_info": n_i})



@login_is_required
def node_details_pod_list(request):
    print('==========')
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    node_name = request.GET.get("node_name", None)

    data = []
    try:
        for pod in core_api.list_pod_for_all_namespaces().items:
            name = pod.spec.node_name
            pod_name = pod.metadata.name
            namespace = pod.metadata.namespace
            status = ("运行中" if pod.status.conditions[-1].status else "异常")
            host_network = pod.spec.host_network
            pod_ip = ( "主机网络" if host_network else pod.status.pod_ip)
            create_time = k8s.dt_format(pod.metadata.creation_timestamp)

            if name == node_name:
                if len(pod.spec.containers) == 1:
                    cpu_requests = "0"
                    cpu_limits = "0"
                    memory_requests = "0"
                    memory_limits = "0"
                    for c in pod.spec.containers:
                        # c_name = c.name
                        # c_image= c.image
                        cpu_requests = "0"
                        cpu_limits = "0"
                        memory_requests = "0"
                        memory_limits = "0"
                        if c.resources.requests is not None:
                            if "cpu" in c.resources.requests:
                                cpu_requests = c.resources.requests["cpu"]
                            if "memory" in c.resources.requests:
                                memory_requests = c.resources.requests["memory"]
                        if c.resources.limits is not None:
                            if "cpu" in c.resources.limits:
                                cpu_limits = c.resources.limits["cpu"]
                            if "memory" in c.resources.limits:
                                memory_limits = c.resources.limits["memory"]
                else:
                    c_r = "0"
                    c_l = "0"
                    m_r = "0"
                    m_l = "0"
                    cpu_requests = ""
                    cpu_limits = ""
                    memory_requests = ""
                    memory_limits = ""
                    for c in pod.spec.containers:
                        c_name = c.name
                        # c_image= c.image
                        if c.resources.requests is not None:
                            if "cpu" in c.resources.requests:
                                c_r = c.resources.requests["cpu"]
                            if "memory" in c.resources.requests:
                                m_r = c.resources.requests["memory"]
                        if c.resources.limits is not None:
                            if "cpu" in c.resources.limits:
                                c_l = c.resources.limits["cpu"]
                            if "memory" in c.resources.limits:
                                m_l = c.resources.limits["memory"]

                        cpu_requests += "%s=%s<br>" % (c_name, c_r)
                        cpu_limits += "%s=%s<br>" % (c_name, c_l)
                        memory_requests += "%s=%s<br>" % (c_name, m_r)
                        memory_limits += "%s=%s<br>" % (c_name, m_l)

                pod = {"pod_name": pod_name, "namespace": namespace, "status": status, "pod_ip": pod_ip,
                    "cpu_requests": cpu_requests, "cpu_limits": cpu_limits, "memory_requests": memory_requests,
                    "memory_limits": memory_limits,"create_time": create_time}
                data.append(pod)

        page = int(request.GET.get('page',1))
        limit = int(request.GET.get('limit'))
        start = (page - 1) * limit
        end = page * limit
        data = data[start:end]
        count = len(data)
        code = 0
        msg = "获取数据成功"

    except Exception as e:
        print(e)
        status = getattr(e, "status")
        if status == 403:
            msg = "没有访问权限！"
        else:
            msg = "查询失败！"

    res = {"code": code, "msg": msg, "count": count, "data": data}
    return JsonResponse(res)


def namespaces(request):
    return render(request, 'k8s/namespaces.html')


def namespaces_api(request):
    """
    判断是否登陆过？
        没有：就是，跳转到登陆页面
        已经登陆，就根据写入到session中的字典信息，获取其token或者kubeconfig信息，向api-server发起认证，成功后，请求所有的ns接口
            然后讲结果封装后返回，由前端展示，并保存
    :param request:
    :return:
    """
    msg = ""
    code = 0

    # 登陆后写入了session信息，然后从中提取认证类型，和相关值，
    auth_type = request.session.get('auth_type')
    token = request.session.get('token') # token或者是kubeconfig在服务端随即生成的文件名，
    # 由功能函数进行认证
    k8s.load_auth_config(auth_type, token)

    # 认证后开始请求所有的命名空间
    core_api = client.CoreV1Api()
    if request.method == "GET":
        search_key = request.GET.get("search_key")
        data = []
        try:
            for ns in core_api.list_namespace().items:
                name = ns.metadata.name
                labels = ns.metadata.labels
                create_time = ns.metadata.creation_timestamp
                namespace = {'name':name,'labels':labels,'create_time':create_time}
                # 根据搜索值返回数据
                if search_key:
                    if search_key in name:
                        data.append(namespace)
                else:
                    data.append(namespace)
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

        # 分页
        if request.GET.get('page'): # layui的数据表格，自动传入查询参数，page=xx&limit=xx
            page = int(request.GET.get('page',1))
            limit = int(request.GET.get('limit'))
            start = (page - 1) * limit
            end = page * limit
            data = data[start:end]

        res = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(res)
    elif request.method == "DELETE":
        # 接收前端传入的数据，然后取出ns的名称，调用k8s客户端api进行删除，删除成功、或失败，都将数据封装后返回，供前端展示
        request_info = QueryDict(request.body) # django本身不支持request.DELETE.get("key")所有经过QueryDict转化下
        ns_name = request_info.get("name")
        print(ns_name)
        try:
            core_api.delete_namespace(ns_name)
            code = 0
            msg = "删除命名空间成功"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "删除权限不足"
            else:
                msg = "删除失败"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)
    elif request.method == 'POST':
        ns_name = request.POST.get('name')

        for ns in core_api.list_namespace().items:
            if ns_name == ns.metadata.name:
                res = {'code': 1, 'msg': '命名空间已经存在'}
                return JsonResponse(res)

        body = client.V1Namespace(
            api_version='v1',
            kind='Namespace',
            metadata=client.V1ObjectMeta(
                name=ns_name
            )
        )
        try:
            core_api.create_namespace(body)
            msg = "创建成功"
        except Exception as e:
            code = 1
            status  = getattr(e, 'status')
            if status == 403:
                msg = "权限不足"
            else:
                msg = "其他日常"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)



@login_is_required
def pvs(request):
    return render(request, 'k8s/pvs.html')


@login_is_required
def pvs_create(request):
    return render(request, 'k8s/pvs_create.html')


@login_is_required
def pvs_api(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)

    core_api = client.CoreV1Api()

    code = 0
    msg = ""
    count = 0
    data = []

    if request.method == 'GET':
        try:
            search_key = request.GET.get('search_key')
            for pv in core_api.list_persistent_volume().items:
                name = pv.metadata.name
                capacity = pv.spec.capacity["storage"]
                access_modes = pv.spec.access_modes
                reclaim_policy = pv.spec.persistent_volume_reclaim_policy
                status = pv.status.phase
                if pv.spec.claim_ref is not None:   # pv是否绑定pvc的信息展示
                    pvc_ns = pv.spec.claim_ref.namespace
                    pvc_name = pv.spec.claim_ref.name
                    pvc = "%s / %s" % (pvc_ns, pvc_name)
                else:
                    pvc = "未绑定"
                storage_class = pv.spec.storage_class_name
                create_time = pv.metadata.creation_timestamp
                pv = {"name": name, "capacity": capacity, "access_modes": access_modes,
                      "reclaim_policy": reclaim_policy, "status": status, "pvc": pvc,
                      "storage_class": storage_class, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(pv)
                else:
                    data.append(pv)

                msg = "查询pv数据成功"

        except Exception as e:
            status = getattr(e, 'status')
            if status == 404:
                msg = "权限不足"
                code = 404
            else:
                msg = "查询pv数据异常"
                code = 500

        res = {'code': code, 'msg': msg, 'count': len(data), 'data': data}
        return JsonResponse(res)
    elif request.method == 'POST':
        try:
            name = request.POST.get("name", None)
            capacity = request.POST.get("capacity", None)
            access_mode = request.POST.get("access_mode", None)
            storage_type = request.POST.get("storage_type", None)
            server_ip = request.POST.get("server_ip", None)
            mount_path = request.POST.get("mount_path", None)

            body = client.V1PersistentVolume(
                api_version="v1",
                kind="PersistentVolume",
                metadata=client.V1ObjectMeta(name=name),
                spec=client.V1PersistentVolumeSpec(
                    capacity={'storage': capacity},
                    access_modes=[access_mode],
                    nfs=client.V1NFSVolumeSource(
                        server=server_ip,
                        path="/ifs/kubernetes/%s" % mount_path
                    )
                )
            )
            core_api.create_persistent_volume(body=body)
            msg = "创建pv成功"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 404:
                msg = "权限不足"
                code = 404
            else:
                msg = "创建pv数据异常"
                code = 500

        res = {'code': code, 'msg': msg}
        return JsonResponse(res)
    elif request.method == 'DELETE':
        request_data = QueryDict(request.body)
        name = request_data.get('name')
        try:
            core_api.delete_persistent_volume(name=name)
            msg = "删除pv成功"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 404:
                msg = "权限不足"
                code = 404
            else:
                msg = "删除pv数据异常"
                code = 500

        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

