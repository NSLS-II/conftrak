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
