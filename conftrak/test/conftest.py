import pytest

from ..ignition import start_server
import uuid
import sys
import time as ttime
import subprocess
import contextlib

@contextlib.contextmanager
def conftrak():
    testing_config = dict(mongo_uri='mongodb://localhost',
                      database='conftrak_test'+str(uuid.uuid4()), serviceport=7771,
                      tzone='US/Eastern')
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
        yield
