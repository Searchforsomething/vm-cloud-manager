import unittest
from unittest.mock import patch, MagicMock
import os
from main import (
    get_auth_token_requester,
    initialize_sdk,
    get_all_folders,
    get_vms,
    stop_vm,
    check_and_stop_expired_vms_in_all_folders
)
from datetime import datetime

class TestMain(unittest.TestCase):

    @patch.dict(os.environ, {
        'OAUTH_TOKEN': 'test_oauth_token',
        'ORGANIZATION_ID': 'test_organization_id'
    })
    @patch('main.SDK')
    @patch('main.requests.get')
    def test_metadata_auth(self, mock_get, mock_sdk):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token"}
        mock_get.return_value = mock_response

        auth = get_auth_token_requester(metadata_addr="169.254.169.254")
        token = auth.get_token()

        self.assertEqual(token, "test_access_token")
        mock_get.assert_called_once()

    @patch('main.SDK')
    def test_token_auth(self, mock_sdk):
        auth = get_auth_token_requester(token="test_token")
        token_request = auth.get_token_request()

        self.assertEqual(token_request.yandex_passport_oauth_token, "test_token")

    @patch('main.SDK')
    def test_initialize_sdk(self, mock_sdk):
        sdk = initialize_sdk("test_oauth_token")
        self.assertIsNotNone(sdk)
        mock_sdk.assert_called_once_with(token="test_oauth_token")

    @patch('main.SDK')
    def test_get_all_folders(self, mock_sdk):
        sdk_instance = mock_sdk.return_value
        mock_client = sdk_instance.client.return_value
        mock_response = MagicMock()
        mock_response.folders = ["folder1", "folder2"]
        mock_client.List.return_value = mock_response

        folders = get_all_folders(sdk_instance, "test_organization_id")
        self.assertEqual(folders, ["folder1", "folder2"])

    @patch('main.SDK')
    def test_get_vms(self, mock_sdk):
        sdk_instance = mock_sdk.return_value
        mock_client = sdk_instance.client.return_value
        mock_response = MagicMock()
        mock_response.instances = ["vm1", "vm2"]
        mock_client.List.return_value = mock_response

        vms = get_vms(sdk_instance, "test_folder_id")
        self.assertEqual(vms, ["vm1", "vm2"])

    @patch('main.SDK')
    def test_stop_vm(self, mock_sdk):
        sdk_instance = mock_sdk.return_value
        mock_client = sdk_instance.client.return_value
        mock_operation = MagicMock()
        mock_client.Stop.return_value = mock_operation

        operation = stop_vm(sdk_instance, "test_vm_id")
        self.assertEqual(operation, mock_operation)

    @patch.dict(os.environ, {
        'OAUTH_TOKEN': 'test_oauth_token',
        'ORGANIZATION_ID': 'test_organization_id'
    })
    @patch('main.get_all_folders')
    @patch('main.get_vms')
    @patch('main.stop_vm')
    @patch('main.SDK')
    @patch('main.datetime', wraps=datetime)
    def test_check_and_stop_expired_vms_in_all_folders(self, mock_datetime, mock_sdk, mock_stop_vm, mock_get_vms, mock_get_all_folders):
        sdk_instance = mock_sdk.return_value

        current_date = datetime(2024, 6, 19)
        mock_datetime.now.return_value = current_date

        mock_folder = MagicMock()
        mock_folder.id = "folder1"
        mock_get_all_folders.return_value = [mock_folder]

        mock_vm = MagicMock()
        mock_vm.id = "vm1"
        mock_vm.labels = {"expired_date": "18.06.2024"}
        mock_get_vms.return_value = [mock_vm]

        mock_vm_details = MagicMock()
        mock_vm_details.status = 2
        sdk_instance.client.return_value.Get.return_value = mock_vm_details

        check_and_stop_expired_vms_in_all_folders()

        mock_stop_vm.assert_called_once_with(sdk_instance, "vm1")

    @patch.dict(os.environ, {
        'OAUTH_TOKEN': 'test_oauth_token',
        'ORGANIZATION_ID': 'test_organization_id'
    })
    @patch('main.get_all_folders')
    @patch('main.get_vms')
    @patch('main.SDK')
    @patch('main.datetime', wraps=datetime)
    def test_check_and_stop_expired_vms_in_all_folders_not_running(self, mock_datetime, mock_sdk, mock_get_vms, mock_get_all_folders):
        sdk_instance = mock_sdk.return_value

        current_date = datetime(2024, 6, 19)
        mock_datetime.now.return_value = current_date

        mock_folder = MagicMock()
        mock_folder.id = "folder1"
        mock_get_all_folders.return_value = [mock_folder]

        mock_vm = MagicMock()
        mock_vm.id = "vm1"
        mock_vm.labels = {"expired_date": "18.06.2024"}
        mock_get_vms.return_value = [mock_vm]

        mock_vm_details = MagicMock()
        mock_vm_details.status = 3  # VM is not running
        sdk_instance.client.return_value.Get.return_value = mock_vm_details

        check_and_stop_expired_vms_in_all_folders()

        sdk_instance.client.return_value.Stop.assert_not_called()

if __name__ == '__main__':
    unittest.main()
