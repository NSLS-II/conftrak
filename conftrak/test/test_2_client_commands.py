from doct import Document
import time as ttime
import pytest
from .utils import testing_config as TESTING_CONFIG
from conftrak.client.commands import ConfigurationReference
from conftrak.exceptions import ConfTrakNotFoundException
from requests.exceptions import HTTPError, RequestException

import uuid
import ujson
import jsonschema

configs_uids = []
document_insertion_times = []


def test_commands_smoke():
    c_create = ConfigurationReference.create
    c_find = ConfigurationReference.find
    c_update = ConfigurationReference.update
    c_delete = ConfigurationReference.delete
    c_get_schema = ConfigurationReference.get_schema


def test_configuration_constructor(conftrak_server):
    c2 = ConfigurationReference()


def test_connection_switch(conftrak_server, conftrak_client):
    conftrak_client.host = 'blah'
    pytest.raises(RequestException, conftrak_client.create, 'test_beamline')
    conftrak_client.host = TESTING_CONFIG['mongohost']
    conftrak_client.create(beamline_id='lix')


def test_configuration_create(conftrak_server, conftrak_client):
    c1 = conftrak_client.create(beamline_id='test')
    c2 = conftrak_client.create(beamline_id='test', uid=str(uuid.uuid4()))
    c_kwargs = dict(key='detector', params={'model':'Pilatus1M',
                                            'vendor':'Dectris'})
    c3 = conftrak_client.create(beamline_id='test', **c_kwargs)


def test_configuration_find(conftrak_server, conftrak_client):
    config_data = dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                       active=True, time= ttime.time(),key='test_config',
                       params=dict(param1='test1', param2='test2'))

    conftrak_client.create(**config_data)
    c_ret = next(conftrak_client.find(uid=config_data['uid'], as_document=True))
    assert c_ret == Document('Configuration', config_data)


def test_configuration_update(conftrak_server, conftrak_client):
    config_data = dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                       active=True, time= ttime.time(),key='test_config',
                       params=dict(param1='test1', param2='test2'))
    conftrak_client.create(**config_data)
    conftrak_client.update(query={'uid': config_data['uid']},
                      update={'key': 'updated_key'})
    updated_conf = next(conftrak_client.find(uid=config_data['uid']))
    assert updated_conf['key'] == 'updated_key'


def test_configuration_delete(conftrak_server, conftrak_client):
    config_data = dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                       active=True, time= ttime.time(),key='test_config',
                       params=dict(param1='test1', param2='test2'))
    conftrak_client.create(**config_data)
    inserted = next(conftrak_client.find(uid=config_data['uid']))
    # Make sure that it was inserted
    assert inserted is not None
    conftrak_client.delete([config_data['uid']])
    with pytest.raises(ConfTrakNotFoundException):
        deleted = next(conftrak_client.find(uid=config_data['uid']))


def test_configuration_find_all(conftrak_server, conftrak_client):
    config_data = dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                       active=True, time= ttime.time(),key='test_config',
                       params=dict(param1='test1', param2='test2'))
    conftrak_client.create(**config_data)
    inserted = next(conftrak_client.find(uid=config_data['uid']))
    # Make sure that it was inserted
    assert inserted is not None
    conftrak_client.delete([config_data['uid']])
    deleted = next(conftrak_client.find(active_only=False, uid=config_data['uid']))
    assert deleted is not None


def test_configuration_schema(conftrak_server, conftrak_client):
    config_data = dict(beamline_id='test_bl', uid=str(uuid.uuid4()),
                       active=True, time=ttime.time(),key='test_config',
                       params=dict(param1='test1', param2='test2'))
    schema = conftrak_client.get_schema()
    try:
        jsonschema.validate(config_data, schema)
    except:
        pytest.fail("test_configuration_schema failed on validate schema.")

