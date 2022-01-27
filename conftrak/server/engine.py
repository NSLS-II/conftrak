from __future__ import absolute_import
from tornado import gen
import tornado.web
import pymongo
import jsonschema
import ujson
from . import utils
from jsonschema.exceptions import ValidationError, SchemaError
from ..exceptions import ConfTrakException


def db_connect(database, mongo_host, mongo_port):
    """Helper function to deal with stateful connections to MongoDB
    Connection established lazily. Connects to the database on request.
    Same connection pool is used for all clients per recommended by
    tornado developer manual.
    Parameters
    ----------
    database: str
        The name of database pymongo creates and/or connects
    host: str
        Name/address of the server that mongo daemon lives
    port: int
        Port num of the server
    Returns pymongo.database.Database
    -------
        Async server object which comes in handy as server has to juggle
    multiple clients and makes no difference for a single client compared
    to pymongo
    """
    try:
        client = pymongo.MongoClient(host=mongo_host, port=mongo_port)
        client.list_database_names()  # check if the server is really okay.
    except (pymongo.errors.ConnectionFailure,
            pymongo.errors.ServerSelectionTimeoutError):
        raise ConfTrakException("Unable to connect to MongoDB server...")

    database = client[database]

    database.configuration.create_index([('uid', pymongo.DESCENDING)],
                                        unique=True, background=False)
    database.configuration.create_index([('time', pymongo.DESCENDING)],
                                        unique=False, background=True)
    database.configuration.create_index([('beamline_id', pymongo.DESCENDING)],
                                        unique=False, background=True,
                                        sparse=True)
    database.configuration.create_index([('key', pymongo.DESCENDING)],
                                        unique=False, background=True,
                                        sparse=True)

    return database


class DefaultHandler(tornado.web.RequestHandler):
    """DefaultHandler which takes care of CORS. Javascript needs this.
    In general, methods on RequestHandler and elsewhere in Tornado
    are not thread-safe. In particular, methods such as write(),
    finish(), and flush() must only be called from the main thread.
    If you use multiple threads it is important to use IOLoop.add_callback
    to transfer control back to the main thread before finishing the request.
    """
    @gen.coroutine
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Access-Control-Max-Age', 1000)
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Content-type', 'application/json')

    def data_received(self, chunk):
        """Abstract method, overwrite potential default"""
        pass


class ConfigurationReferenceHandler(DefaultHandler):
    """Handler for ConfigurationReference insert, update, and querying.
    A RESTful handler, nothing fancy or stateful about this
    Methods
    --------
    get()
        Query 'configuration_referenece' documents given certain parameters.
    Pass 'num' in order to obtain the last 'num' configuration references.
    post()
        Insert 'configuration' documents
    put()
        Update or Insert if 'configuration' document does not exist.
    Update supports both field update and document replacement. If you
    would like to replace a document, simply provide a full doc in update
    field. Otherwise, provide a dict that holds the new value and field name.
    Returns the total number of documents that are updated.
    """
    @gen.coroutine
    def get(self):
        database = self.settings['db']
        query = utils.unpack_params(self)
        if 'active_only' in query:
            filter_active = query.pop('active_only')
            if filter_active:
                query['active'] = True

        num = query.pop("num", None)
        try:
            if num:
                docs = database.configuration.find(query).sort('time',
                                                               direction=pymongo.DESCENDING).limit(num)
            else:
                docs = database.configuration.find(query).sort('time',
                                                               direction=pymongo.DESCENDING)
            num_docs = database.configuration.count_documents(query)
            if docs and num_docs > 0:
                utils.return2client(self, docs)
            else:
                raise utils._compose_err_msg(500, 'No results found!')
        except pymongo.errors.PyMongoError:
            raise utils._compose_err_msg(500, 'Query on config has failed',
                                         query)


    @gen.coroutine
    def post(self):
        database = self.settings['db']
        data = ujson.loads(self.request.body.decode("utf-8"))
        uids = []
        if isinstance(data, list):
            for d in data:
                # Ensure the active status on the new Configuration
                d['active'] = True
                d = utils.default_timeuid(d)
                try:
                    jsonschema.validate(d,
                                        utils.schemas['configuration'])
                except (ValidationError, SchemaError):
                    raise utils._compose_err_msg(400,
                                                 "Invalid schema on document(s)", d)
                uids.append(d['uid'])
                database.configuration.insert_one(d)
        elif isinstance(data, dict):
            data = utils.default_timeuid(data)
            # Ensure the active status on the new Configuration
            data['active'] = True
            try:
                jsonschema.validate(data,
                                    utils.schemas['configuration'])
            except (ValidationError, SchemaError):
                raise utils._compose_err_msg(400,
                                             "Invalid schema on document(s)", data)
            uids.append(data['uid'])
            database.configuration.insert_one(data)
        else:
            raise utils._compose_err_msg(500,
                                         status='ConfigurationHandler expects list or dict') 
        self.finish(ujson.dumps(uids))

    @gen.coroutine
    def put(self):
        database = self.settings['db']
        incoming = ujson.loads(self.request.body)
        try:
            query = incoming.pop('query')
            update = incoming.pop('update')
        except KeyError:
            raise utils._compose_err_msg(500,
                                         status='filter and update are both required fields')
        if any(x in update.keys() for x in ['uid', 'time']):
            raise utils._compose_err_msg(500,
                                   status='Time and uid cannot be updated')
        res = database.configuration.update_many(filter=query,
                                           update={'$set': update},
                                           upsert=False)
        self.finish(ujson.dumps(res.raw_result))

    @gen.coroutine
    def delete(self):
        database = self.settings['db']
        incoming = utils.unpack_params(self)
        #incoming = ujson.loads(self.request.body)
        try:
            uid_list = incoming.pop('uid_list')
        except KeyError:
            raise utils._compose_err_msg(500,
                                         status='delete require a list of uids')

        if not isinstance(uid_list, (list, tuple)):
            uid_list = [uid_list]

        res = database.configuration.update_many(filter={'uid': {'$in': uid_list}},
                                                 update={'$set': {'active': False}},
                                                 upsert=False)
        self.finish(ujson.dumps(res.raw_result))


class SchemaHandler(DefaultHandler):
    """Provides the json used for schema validation provided collection name"""
    @gen.coroutine
    def get(self):
        col = utils.unpack_params(self)
        self.write(utils.schemas[col])
        self.finish()

    @gen.coroutine
    def put(self):
        raise utils._compose_err_msg(405,
                                     status='Not allowed on server')

    @gen.coroutine
    def post(self):
        raise utils._compose_err_msg(405,
                                     status='Not allowed on server')
