import pytest

from conftrak.ignition import start_server
import uuid
import sys
import time as ttime
import subprocess
import contextlib
from conftrak.client.commands import ConfigurationReference

testing_config = dict(mongo_uri='mongodb://localhost', mongo_host="localhost",
                    database='conftrak_test'+str(uuid.uuid4()), serviceport=7771,
                    tzone='US/Eastern', log_file_prefix="", testing=True)

@contextlib.contextmanager
def conftrak():
    try:
        ps = subprocess.Popen(
            [
           sys.executable,
                "-c",
                f"from conftrak.ignition import start_server; start_server(args={testing_config})",
            ]
        )
        ttime.sleep(4)
        yield ps
    finally:
        ps.terminate()


@pytest.fixture(scope="session")
def conftrak_fixture():
    with conftrak() as conftrak_fixture:
        print(conftrak_fixture)
        yield

@pytest.fixture(scope='function')
def conftrak_client():
    c = ConfigurationReference(host=testing_config["mongo_host"],port=testing_config["serviceport"])
    return c

def test_conftrak_fixture(conftrak_fixture, conftrak_client):
    print(conftrak_client)
    print(conftrak_client.get_schema())
    print(list(conftrak_client.find()))

