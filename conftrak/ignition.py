from __future__ import absolute_import
import argparse
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
from .server.engine import (ConfigurationReferenceHandler, SchemaHandler,
                            db_connect)
from .server.conf import load_configuration


class Application(tornado.web.Application):
    def __init__(self, db):
        handlers = [(r'/configuration', ConfigurationReferenceHandler),
                    (r'/schema', SchemaHandler)]
        settings = {'db': db}

        tornado.web.Application.__init__(self, handlers, **settings)


def parse_configuration(config=None):
    if not config:
        config = {k: v for k, v in
                  load_configuration('conftrak', 'CFTRK',
                                     ['mongo_host', 'mongo_port', 'timezone',
                                      'database', 'service_port'],
                                     allow_missing=True).items()
                  if v is not None}
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', dest='database', type=str,
                        help='name of database to use')
    parser.add_argument('--mongo-uri',dest='mongo_uri', type=str,
                        help='URI to use to connect to Mongo')
    parser.add_argument('--timezone', dest='timezone', type=str,
                        help='Local timezone')
    parser.add_argument('--service-port', dest='service_port', type=int,
                        help='port listen to for clients')
    parser.add_argument('--log_file_prefix', dest='log_file_prefix', type=str,
                        help='Log file name that tornado logs are dumped')
    args = parser.parse_known_args()[0]
    if args.database is not None:
        config['database'] = args.database
    if args.mongo_uri is not None:
        config['mongo_uri'] = args.mongo_uri
    if args.timezone is not None:
        config['timezone'] = args.timezone
    service_port = args.service_port
    if service_port is None:
        service_port = 7771

    config['service_port'] = service_port
    config['log_file_prefix'] = args.log_file_prefix
    return config


def start_server(args=None):
    """
    ConfTrak service startup script.
    Returns tornado event loop provided configuration.

    Parameters
    ----------
    config: dict
        Command line arguments always have priority over local config or yaml
        files. Using these parameters, a tornado event loop is created. Keep
        in mind that this server is started in lazy fashion. It does not verify
        the existence of a mongo instance running on the specified location.
    """
    global server
    config = parse_configuration(args)
    db = db_connect(config['database'],
                    config['mongo_uri'])

    tornado.options.parse_command_line({'log_file_prefix':
                                        config['log_file_prefix']})
    app = Application(db)
    print('Starting ConfTrak service with configuration ', config)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(config['service_port'])

    tornado.ioloop.IOLoop.current().start()
