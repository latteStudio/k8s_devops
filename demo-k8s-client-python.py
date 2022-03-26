"""
eyJhbGciOiJSUzI1NiIsImtpZCI6IlF6cWwtbFZhQlF2Sy1sXzN0OVBXMldKSWhlM1dvTlRTS0JVVmFxMWxNZjAifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJkYXNoYm9hcmQtYWRtaW4tdG9rZW4tZHhkN2IiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGFzaGJvYXJkLWFkbWluIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiZWVjNDc2NzMtZTRlMy00MzFlLTk1NzEtNjhlNjgwNWQwM2Q2Iiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50Omt1YmUtc3lzdGVtOmRhc2hib2FyZC1hZG1pbiJ9.b8q4HDf_GrUl8mqvfP3AT4I9n43ZKU4eMFMulG8MeW_Hrc8yoLPT5q3oRtWHV-zCQL6j_g4JT7FagHg0rFWsZ4VGdQeCek7zmvJUlIzFLGHdJETYn8Zo3oYThHftAOmsrSgLFKhkIUIIbpteWUL6L7p6KLqPdMVSkft5TRul0yYGYDV1L2bBU9XfbAmgnvxqWSfMXm69xbOKauZJhv9FvWOrV13INIcq1fNBV2bmdaT9g8QGor_VGau6wDAlNU3jA12nzHImTHK4VTRUqi1-2ZfuH6gRdMmho753eCk-AiUgwyQQe_MflhNGvh_LjZcbU2Hi1saczYpYv-uiENdEpA
"""
from kubernetes import client, config

# Configs can be set in Configuration class directly or using helper utility

# 认证1：https证书认证，把k8s集群的kube_conf搞过来，给库用

# 通过配置文件，认证并访问k8s api
# kube_config_file_path = r'.\conf\kube_conf'
# config.load_kube_config(kube_config_file_path)

# 认证2：http  token认证，创建sa，绑定到cluster-admin角色，然后把其secrets中的token取出，
# 还需要api的url、ca证书
# 通过token认证：
from kubernetes import client, config
configuration = client.Configuration()
configuration.host = "https://192.168.80.100:6443"  # APISERVER地址
configuration.ssl_ca_cert = r".\conf\ca.crt"  # CA证书
configuration.verify_ssl = True   # 启用证书验证

token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlF6cWwtbFZhQlF2Sy1sXzN0OVBXMldKSWhlM1dvTlRTS0JVVmFxMWxNZjAifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJkYXNoYm9hcmQtYWRtaW4tdG9rZW4tZHhkN2IiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGFzaGJvYXJkLWFkbWluIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiZWVjNDc2NzMtZTRlMy00MzFlLTk1NzEtNjhlNjgwNWQwM2Q2Iiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50Omt1YmUtc3lzdGVtOmRhc2hib2FyZC1hZG1pbiJ9.b8q4HDf_GrUl8mqvfP3AT4I9n43ZKU4eMFMulG8MeW_Hrc8yoLPT5q3oRtWHV-zCQL6j_g4JT7FagHg0rFWsZ4VGdQeCek7zmvJUlIzFLGHdJETYn8Zo3oYThHftAOmsrSgLFKhkIUIIbpteWUL6L7p6KLqPdMVSkft5TRul0yYGYDV1L2bBU9XfbAmgnvxqWSfMXm69xbOKauZJhv9FvWOrV13INIcq1fNBV2bmdaT9g8QGor_VGau6wDAlNU3jA12nzHImTHK4VTRUqi1-2ZfuH6gRdMmho753eCk-AiUgwyQQe_MflhNGvh_LjZcbU2Hi1saczYpYv-uiENdEpA"
configuration.api_key = {"authorization": "Bearer " + token}  # 指定Token字符串
client.Configuration.set_default(configuration)

apps_api = client.AppsV1Api()

# 查询deployment
for dp in apps_api.list_deployment_for_all_namespaces().items:
    print(dp.metadata.name)

# 创建
namespace = "default"
name = "api-test"
replicas = 3
labels = {'a':'1', 'b':'2'}  # 不区分数据类型，都要加引号
image = "nginx"
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
                            name="web",
                            image=image
                        )]
                    )
                ),
            )
        )
try:
    apps_api.create_namespaced_deployment(namespace=namespace, body=body)
except Exception as e:
    status = getattr(e, "status")
    if status == 400:
        print(e)
        print("格式错误")
    elif status == 403:
        print("没权限")


ns = 'default'
name = 'api-test'
apps_api.delete_namespaced_deployment(name, ns)


"""
svc操作
"""

core_api = client.CoreV1Api()
# 查询
for svc in core_api.list_namespaced_service(namespace="default").items:
    print(svc.metadata.name)

# 创建
namespace = "default"
name = "api-test"
selector = {'a':'1', 'b':'2'}  # 不区分数据类型，都要加引号
port = 80
target_port = 80
type = "NodePort"
body = client.V1Service(
    api_version="v1",
    kind="Service",
    metadata=client.V1ObjectMeta(
        name=name
    ),
    spec=client.V1ServiceSpec(
        selector=selector,
        ports=[client.V1ServicePort(
            port=port,
            target_port=target_port
        )],
        type=type
    )
)
core_api.create_namespaced_service(namespace=namespace, body=body)

# 删除
core_api.delete_namespaced_service(namespace=namespace, name=name)