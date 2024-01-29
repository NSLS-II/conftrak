from doct import Document
import ujson
import requests
from ..client import conf
from .utils import _get, _post, _put, _delete


class ConfigurationReference(object):
    """Reference implementation of generic configuration manager"""

    def __init__(self, host=conf.conn_config["host"], port=conf.conn_config["port"]):
        """Constructor

        Parameters
        ----------
        host: str, optional
            Machine name/address for ConfTrak server
        port: int, optional
            Port ConfTrak server is initiated on

        """
        self.host = host
        self.port = port

    @property
    def _server_path(self):
        """URL to the ConfTrak server"""
        return "http://{}:{}/".format(self.host, self.port)

    @property
    def _conf_url(self):
        """URL to the configuration reference handler in the server side"""
        return self._server_path + "configuration"

    @property
    def _schema_url(self):
        """URL to the schema reference handler in the server side"""
        return self._server_path + "schema"

    def create(self, beamline_id, time=None, uid=None, **kwargs):
        """Insert a configuration to the database

        Parameters
        ----------
        beamline_id : str
            The beamline identifier.
        time : float
            The time that the configuration was created.
        uid : str
            Unique identifier for a configuration document

        Returns
        -------
        ins_doc : str
            The inserted document

        """
        doc = dict(uid=uid, beamline_id=beamline_id, time=time, **kwargs)
        ins_doc = _post(self._conf_url, doc)
        return ins_doc[0]

    def update(self, query, update):
        """Update a configuration given a query and name value pair to be
        updated. No upsert support. For more info on upsert, check Mongo
        documentations.

        Parameters
        -----------
        query: dict
            Allows finding Sample documents to be updated
        update: dict
            Name/value pair that is to be replaced within an existing Request doc

        Returns
        ----------
        bool
            Returns True if update successful

        """
        _put(self._conf_url, query, update)
        return True

    def find(self, as_document=False, active_only=True, **kwargs):
        """
        Parameters
        ----------
        as_document: bool
            Formats output to doct.Document if True
        active_only: bool
            Retrieve only active configurations. Default is True

        Yields
        ------
        c: dict, doct.Document
            Documents which have all keys with the given values

        """
        kwargs["active_only"] = active_only
        content = _get(self._conf_url, params=kwargs)
        if as_document:
            for c in content:
                yield Document("Configuration", c)
        else:
            for c in content:
                yield c

    def delete(self, uid_list):
        """Virtually delete (mark as inactive) the informed configurations.

        Parameters
        ----------
        uid_list: list
            List of unique identifiers to be marked as inactive.

        """
        _delete(self._conf_url, params={"uid_list": uid_list})
        return True

    def get_schema(self):
        """Get information about schema from server side

        Returns
        -------
        dict
            Returns the json schema dict used for validation

        """
        r = requests.get(self._schema_url, params=ujson.dumps("configuration"))
        r.raise_for_status()
        return ujson.loads(r.text)
