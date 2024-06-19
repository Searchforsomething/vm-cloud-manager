import os
from datetime import datetime
from typing import Optional, Union
from dotenv import load_dotenv
import requests
from yandexcloud import SDK
from yandex.cloud.iam.v1.iam_token_service_pb2 import CreateIamTokenRequest
from yandex.cloud.resourcemanager.v1 import folder_service_pb2_grpc, folder_service_pb2
from yandex.cloud.compute.v1 import instance_service_pb2_grpc, instance_service_pb2

_MDS_ADDR = "169.254.169.254"
_MDS_URL = "http://{}/computeMetadata/v1/instance/service-accounts/default/token"
_MDS_HEADERS = {"Metadata-Flavor": "Google"}
_MDS_TIMEOUT = (1.0, 1.0)  # 1sec connect, 1sec read

YC_API_ENDPOINT = "api.cloud.yandex.net"

load_dotenv()
def set_up_yc_api_endpoint(endpoint: str) -> str:
    global YC_API_ENDPOINT
    YC_API_ENDPOINT = endpoint
    return YC_API_ENDPOINT


def initialize_sdk(oauth_token):
    sdk = SDK(token=oauth_token)
    return sdk


class MetadataAuth:
    def __init__(self, metadata_addr: str):
        self.__metadata_addr = metadata_addr

    def url(self) -> str:
        return _MDS_URL.format(self.__metadata_addr)

    def get_token(self) -> str:
        r = requests.get(self.url(), headers=_MDS_HEADERS, timeout=_MDS_TIMEOUT)
        r.raise_for_status()
        response = r.json()
        return response["access_token"]

class TokenAuth:
    def __init__(self, token: str):
        self.__oauth_token = token

    def get_token_request(self) -> "CreateIamTokenRequest":
        return CreateIamTokenRequest(yandex_passport_oauth_token=self.__oauth_token)


class IamTokenAuth:
    def __init__(self, iam_token: str):
        self.__iam_token = iam_token

    def get_token(self) -> str:
        return self.__iam_token

def get_auth_token_requester(
    token: Optional[str] = None,
    iam_token: Optional[str] = None,
    metadata_addr: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> Union["MetadataAuth", "TokenAuth", "IamTokenAuth"]:
    if endpoint is None:
        endpoint = YC_API_ENDPOINT
    auth_methods = [("token", token), ("iam_token", iam_token)]
    auth_methods = [(auth_type, value) for auth_type, value in auth_methods if value is not None]

    if len(auth_methods) == 0:
        metadata_addr = metadata_addr if metadata_addr is not None else os.environ.get("YC_METADATA_ADDR", _MDS_ADDR)
        return MetadataAuth(metadata_addr)

    if len(auth_methods) > 1:
        raise RuntimeError(f"Conflicting API credentials properties are set: {[auth[0] for auth in auth_methods]}.")

    if token is not None:
        return TokenAuth(token=token)
    if iam_token is not None:
        return IamTokenAuth(iam_token)

    raise RuntimeError("Unknown auth method")

def get_all_folders(sdk, organization_id):
    resource_manager = sdk.client(folder_service_pb2_grpc.FolderServiceStub)
    response = resource_manager.List(folder_service_pb2.ListFoldersRequest(cloud_id=organization_id))
    return response.folders

def get_vms(sdk, folder_id):
    compute = sdk.client(instance_service_pb2_grpc.InstanceServiceStub)
    response = compute.List(instance_service_pb2.ListInstancesRequest(folder_id=folder_id))
    return response.instances

def stop_vm(sdk, vm_id):
    compute = sdk.client(instance_service_pb2_grpc.InstanceServiceStub)
    operation = compute.Stop(instance_service_pb2.StopInstanceRequest(instance_id=vm_id))
    return operation

def check_and_stop_expired_vms_in_all_folders():
    # Загрузка параметров аутентификации
    oauth_token = os.getenv('OAUTH_TOKEN')

    auth_method = get_auth_token_requester(token=oauth_token)

    if isinstance(auth_method, TokenAuth):
        oauth_token = auth_method._TokenAuth__oauth_token
    else:
        raise RuntimeError("Unsupported authentication method")

    sdk = initialize_sdk(oauth_token)

    # Получение списка всех каталогов
    organization_id = os.getenv('ORGANIZATION_ID')
    folders = get_all_folders(sdk, organization_id)

    current_date = datetime.now()

    for folder in folders:
        folder_id = folder.id
        vms = get_vms(sdk, folder_id)

        for vm in vms:
            labels = vm.labels
            expired_date_str = labels.get("expired_date")

            if expired_date_str:
                expired_date = datetime.strptime(expired_date_str, "%d.%m.%Y")
                if expired_date < current_date:
                    try:
                        # Check if VM is running
                        vm_details = sdk.client(instance_service_pb2_grpc.InstanceServiceStub).Get(
                            instance_service_pb2.GetInstanceRequest(instance_id=vm.id)
                        )
                        # Check if the VM status indicates it's running
                        if vm_details.status == 2:
                            stop_vm(sdk, vm.id)
                            print(f"VM {vm.id} in folder {folder_id} stopped successfully.")
                        else:
                            print(f"VM {vm.id} in folder {folder_id} is not running.")
                    except Exception as e:
                        print(f"Failed to stop VM {vm.id} in folder {folder_id}: {e}")
                else:
                    print(f"VM {vm.id} in folder {folder_id} is not expired.")
            else:
                print(f"VM {vm.id} in folder {folder_id} has no expired_date label.")


if __name__ == "__main__":
    check_and_stop_expired_vms_in_all_folders()
