import pytest
from conftrak.ignition import start_server
from mock import patch
import uuid
import sys
import time as ttime
import subprocess
import contextlib
from conftrak.client.commands import ConfigurationReference
from tornado.httpclient import HTTPClient


testing_config = {
    "mongo_uri": "mongodb://localhost",
    "mongo_host": "localhost",
    "database": "conftrak_test" + str(uuid.uuid4()),
    "service_port": 7771,
    "tzone": "US/Eastern",
    "log_file_prefix": "",
}


@contextlib.contextmanager
def conftrak_process():
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
    with conftrak_process() as conftrak_fixture:
        yield


@pytest.fixture(scope="function")
def conftrak_client():
    c = ConfigurationReference(
        host=testing_config["mongo_host"], port=testing_config["service_port"]
    )
    return c


@pytest.fixture(scope="session")
def tornado_client():
    return HTTPClient()
