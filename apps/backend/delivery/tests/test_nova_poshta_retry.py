from unittest import mock

import pytest
import requests

from delivery import tasks
from delivery.providers.nova_poshta.client import NovaPoshtaClient
from delivery.providers.nova_poshta.config import NovaPoshtaConfig

OK_BODY = {"success": True, "data": [{"Ref": "1"}], "errors": []}


def make_response(status=200, body=None):
    response = mock.Mock(status_code=status)
    response.json.return_value = body if body is not None else OK_BODY
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
    else:
        response.raise_for_status.return_value = None
    return response


@pytest.fixture
def client():
    return NovaPoshtaClient(NovaPoshtaConfig(api_key="test", api_url="https://np.test/v2.0/json/"))


@pytest.fixture(autouse=True)
def no_sleep():
    with mock.patch("delivery.providers.nova_poshta.client.time.sleep") as sleep:
        yield sleep


def call(client):
    return client._call("AddressGeneral", "getWarehouses")


@pytest.mark.parametrize("error", [requests.ReadTimeout(), requests.ConnectionError()])
def test_network_error_is_retried(client, error):
    with mock.patch("requests.post", side_effect=[error, make_response()]) as post:
        assert call(client) == OK_BODY["data"]
    assert post.call_count == 2


def test_server_error_is_retried(client):
    with mock.patch("requests.post", side_effect=[make_response(502), make_response()]) as post:
        assert call(client) == OK_BODY["data"]
    assert post.call_count == 2


def test_lasting_outage_fails_after_all_retries(client, no_sleep):
    with mock.patch("requests.post", side_effect=requests.ReadTimeout()) as post:
        with pytest.raises(requests.ReadTimeout):
            call(client)
    assert post.call_count == NovaPoshtaClient.MAX_RETRIES + 1
    assert [c.args[0] for c in no_sleep.call_args_list] == [5, 10, 20, 40, 80]


def test_client_error_is_not_retried(client):
    with mock.patch("requests.post", return_value=make_response(403)) as post:
        with pytest.raises(requests.HTTPError):
            call(client)
    assert post.call_count == 1


def test_api_error_is_not_retried(client):
    body = {"success": False, "data": [], "errors": ["API key expired"]}
    with mock.patch("requests.post", return_value=make_response(body=body)) as post:
        with pytest.raises(ValueError):
            call(client)
    assert post.call_count == 1


def test_rate_limit_is_retried(client):
    limited = {"success": False, "data": [], "errors": ["To many requests"]}
    with mock.patch("requests.post", side_effect=[make_response(body=limited), make_response()]) as post:
        assert call(client) == OK_BODY["data"]
    assert post.call_count == 2


def test_task_retries_later_when_provider_unreachable():
    provider = mock.Mock()
    provider.iter_all_warehouses.side_effect = requests.ReadTimeout()
    with (
        mock.patch.object(tasks, "get_provider", return_value=provider),
        mock.patch.object(tasks.sync_provider_branches, "retry", side_effect=RuntimeError("retry")) as retry,
    ):
        with pytest.raises(RuntimeError, match="retry"):
            tasks.sync_provider_branches.apply(args=["nova_poshta"], throw=True)
    assert retry.call_args.kwargs["countdown"] == tasks.SYNC_RETRY_DELAY_SECONDS
