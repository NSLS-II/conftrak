import pytest
from conftrak.ignition import start_server
from doct import Document
from mock import patch
import ujson
import jsonschema
import uuid
import sys
import time as ttime
import subprocess
import contextlib
from conftrak.client.commands import ConfigurationReference
from conftrak.client.utils import doc_or_uid_to_uid
from conftrak.exceptions import ConfTrakNotFoundException
from conftrak.ignition import parse_configuration
from conftrak.server.engine import db_connect
from conftrak.server.utils import ConfTrakException
from requests.exceptions import RequestException
from tornado.httpclient import AsyncHTTPClient, HTTPResponse


testing_config = {
    "mongo_uri": "mongodb://localhost",
    "mongo_host": "localhost",
    "database": "conftrak_test" + str(uuid.uuid4()),
    "serviceport": 7771,
    "tzone": "US/Eastern",
    "log_file_prefix": "",
}


@contextlib.contextmanager
def conftrak():
    try:
        ps = subprocess.Popen(
            [
                sys.executable,
                "-c",
                f"from conftrak.ignition import start_server; start_server(args={testing_config}, testing=True)",
            ]
        )
        ttime.sleep(4)
        yield ps
    finally:
        ps.terminate()


@pytest.fixture(scope="session")
def conftrak_server():
    with conftrak() as conftrak_fixture:
        print(conftrak_fixture)
        yield


@pytest.fixture(scope="function")
def conftrak_client():
    c = ConfigurationReference(
        host=testing_config["mongo_host"], port=testing_config["serviceport"]
    )
    return c


def get_http_client():
    return AsyncHTTPClient()


# tests on server-side
def test_parse_configuration():
    testargs = [
        "prog",
        "--database",
        "conftrak",
        "--mongo-uri",
        "mongodb://localhost",
        "--timezone",
        "US/Eastern",
    ]
    with patch.object(sys, "argv", testargs):
        config = parse_configuration(dict())
        assert config["service_port"] == 7771


def test_db_connect():
    db_connect(testing_config["database"], testing_config["mongo_uri"])

    with pytest.raises(ConfTrakException):
        db_connect(testing_config["database"], "invalid_mongo_uri")


localhost_url = "http://localhost"
payload1 = dict(
    beamline_id="test_bl",
    uid=str(uuid.uuid4()),
    active=True,
    time=ttime.time(),
    key="test_config",
    params=dict(param1="test1", param2="test2"),
)
payload2 = [
    dict(
        beamline_id="test_bl",
        uid=str(uuid.uuid4()),
        active=True,
        time=ttime.time(),
        key="test_config",
        params=dict(param1="test1", param2="test2"),
    )
]


@pytest.mark.parametrize(
    "url, endpoint, payload, method, response_code, raise_error",
    [
        (localhost_url, "configuration", payload1, "POST", 200, False),
        (localhost_url, "configuration", payload2, "POST", 200, False),
    ],
)
async def test_configuration_post(
    conftrak_fixture, url, endpoint, payload, method, response_code, raise_error
):
    http_client = get_http_client()
    if payload:
        body = ujson.dumps(payload)
    else:
        body = None
    response = await http_client.fetch(
        url, body=body, method=method, raise_error=raise_error
    )
    assert response.code == response_code
