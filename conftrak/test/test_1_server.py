import sys
import uuid
import ujson
import pytest
import time as ttime
from mock import patch
from conftrak.ignition import Application, parse_configuration
from conftrak.server.engine import (db_connect)
from conftrak.server.utils import ConfTrakException
from .utils import testing_config as TESTING_CONFIG


@pytest.fixture
def app():
    db = db_connect(TESTING_CONFIG['database'],
                    TESTING_CONFIG['mongouri'])
    return Application(db)


def test_parse_configuration():
    testargs = ["prog", "--database", "conftrak", "--mongo-uri", "mongodb://localhost",
                "--timezone", "US/Eastern"]
    with patch.object(sys, 'argv', testargs):
        config = parse_configuration(dict())
        assert config['service_port'] == 7771


def test_db_connect():
    db_connect(TESTING_CONFIG['database'],
               TESTING_CONFIG['mongouri'])

    with pytest.raises(ConfTrakException):
        db_connect(TESTING_CONFIG['database'],
                   'invalid_mongo_uri',
                   TESTING_CONFIG['mongouri'])


@pytest.mark.gen_test
def test_configuration_post(http_server, http_client, base_url):
    payload = dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                   active=True, time=ttime.time(), key='test_config',
                   params=dict(param1='test1', param2='test2'))
    url = '{}/{}'.format(base_url, 'configuration')
    body = ujson.dumps(payload)
    response = yield http_client.fetch(url, method='POST', body=body,
                                       raise_error=False)
    assert response.code == 200

    # Test submiting a list
    payload = [dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                    active=True, time=ttime.time(), key='test_config',
                    params=dict(param1='test1', param2='test2'))]
    url = '{}/{}'.format(base_url, 'configuration')
    body = ujson.dumps(payload)
    response = yield http_client.fetch(url, method='POST', body=body,
                                       raise_error=False)
    assert response.code == 200

    # Test invalid schema
    payload = dict(a=1, b=2)
    url = '{}/{}'.format(base_url, 'configuration')
    body = ujson.dumps(payload)
    response = yield http_client.fetch(url, method='POST', body=body,
                                       raise_error=False)
    assert response.code == 400

    payload = [dict(a=1, b=2)]
    url = '{}/{}'.format(base_url, 'configuration')
    body = ujson.dumps(payload)
    response = yield http_client.fetch(url, method='POST', body=body,
                                       raise_error=False)
    assert response.code == 400

    # Test invalid payload format. The handler expects list or dict
    payload = 1
    url = '{}/{}'.format(base_url, 'configuration')
    body = ujson.dumps(payload)
    response = yield http_client.fetch(url, method='POST', body=body,
                                       raise_error=False)
    assert response.code == 500


@pytest.mark.gen_test
def test_configuration_get(http_server, http_client, base_url):
    # Insert the test data
    payload_insert = dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                          active=True, time=ttime.time(), key='test_config',
                          params=dict(param1='test1', param2='test2'))
    url = '{}/{}'.format(base_url, 'configuration')
    body = ujson.dumps(payload_insert)
    response = yield http_client.fetch(url, method='POST', body=body,
                                       raise_error=False)

    url = '{}/{}'.format(base_url, 'configuration')
    body = None

    # Test valid query
    payload = ujson.dumps(dict(active_only=True))
    g_url = url + "?" + payload
    response = yield http_client.fetch(g_url, method='GET', body=body,
                                       raise_error=False)
    assert response.code == 200

    # Test valid query with limit on number of rows
    payload = ujson.dumps(dict(active_only=False, num=1))
    g_url = url + "?" + payload
    response = yield http_client.fetch(g_url, method='GET', body=body,
                                       raise_error=False)
    assert response.code == 200

    # Test valid query without results on DB 
    payload = ujson.dumps(dict(active_only=False, uid="-1"))
    g_url = url + "?" + payload
    response = yield http_client.fetch(g_url, method='GET', body=body,
                                       raise_error=False)
    assert response.code == 500

    # Test invalid query
    payload = ujson.dumps({"$uid":"{'non_existent':1}", "num":1})
    g_url = url + "?" + payload
    response = yield http_client.fetch(g_url, method='GET', body=body,
                                       raise_error=False)
    print("Response: ", response)
    assert response.code == 500


@pytest.mark.gen_test
def test_configuration_put(http_server, http_client, base_url):
    # Insert the test data
    payload_insert = dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                          active=True, time=ttime.time(), key='test_config',
                          params=dict(param1='test1', param2='test2'))
    url = '{}/{}'.format(base_url, 'configuration')
    body = ujson.dumps(payload_insert)
    response = yield http_client.fetch(url, method='POST', body=body,
                                       raise_error=False)

    # Update the key field
    payload_update = dict(query={'uid': payload_insert['uid']},
                          update={'key': 'updated_key'})
    body = ujson.dumps(payload_update)
    response = yield http_client.fetch(url, method='PUT', body=body,
                                       raise_error=False)

    assert response.code == 200

    # Test invalid arguments. Query and Update are required
    payload_update = dict(update={'key': 'updated_key'})
    body = ujson.dumps(payload_update)
    response = yield http_client.fetch(url, method='PUT', body=body,
                                       raise_error=False)

    assert response.code == 500

    # Test invalid update. Updates on UID and Time are not allowed
    payload_update = dict(query={'uid': payload_insert['uid']},
                          update={'uid': 'this_must_be_invalid'})
    body = ujson.dumps(payload_update)
    response = yield http_client.fetch(url, method='PUT', body=body,
                                       raise_error=False)

    assert response.code == 500

    payload_update = dict(query={'uid': payload_insert['uid']},
                          update={'time': ttime.time()})
    body = ujson.dumps(payload_update)
    response = yield http_client.fetch(url, method='PUT', body=body,
                                       raise_error=False)

    assert response.code == 500


@pytest.mark.gen_test
def test_configuration_delete(http_server, http_client, base_url):
    payload_insert = dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                          active=True, time=ttime.time(), key='test_config',
                          params=dict(param1='test1', param2='test2'))
    url = '{}/{}'.format(base_url, 'configuration')
    body = ujson.dumps(payload_insert)
    response = yield http_client.fetch(url, method='POST', body=body,
                                       raise_error=False)

    # Test a valid delete
    payload_delete = dict(uid_list=[payload_insert['uid']])
    d_url = url+"?"+ujson.dumps(payload_delete)
    body = None
    response = yield http_client.fetch(d_url, method='DELETE', body=body,
                                       raise_error=False)

    assert response.code == 200

    # Test delete sending a single uid, not a list
    payload_delete = dict(uid_list=payload_insert['uid'])
    d_url = url+"?"+ujson.dumps(payload_delete)
    body = None
    response = yield http_client.fetch(d_url, method='DELETE', body=body,
                                       raise_error=False)

    assert response.code == 200

    # Test delete must fail if a list of uids is not given.
    payload_delete = dict(my_param=[payload_insert['uid']])
    d_url = url+"?"+ujson.dumps(payload_delete)
    body = None
    response = yield http_client.fetch(d_url, method='DELETE', body=body,
                                       raise_error=False)

    assert response.code == 500


@pytest.mark.gen_test
def test_schema_get(http_server, http_client, base_url):
    url = '{}/{}'.format(base_url, 'schema')
    body = None
    url = url + '?'+ujson.dumps('configuration')
    response = yield http_client.fetch(url, method='GET', body=body,
                                       raise_error=False)
    assert response.code == 200


@pytest.mark.gen_test
def test_schema_put(http_server, http_client, base_url):
    url = '{}/{}'.format(base_url, 'schema')
    body = 'configuration'
    response = yield http_client.fetch(url, method='PUT', body=body,
                                       raise_error=False)
    assert response.code == 405


@pytest.mark.gen_test
def test_schema_post(http_server, http_client, base_url):
    url = '{}/{}'.format(base_url, 'schema')
    body = 'configuration'
    response = yield http_client.fetch(url, method='POST', body=body,
                                       raise_error=False)
    assert response.code == 405
