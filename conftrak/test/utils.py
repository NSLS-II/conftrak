import uuid
import requests
import uuid
import time as ttime
from subprocess import Popen, STDOUT
import os
from pymongo import MongoClient

testing_config = dict(mongouri='mongodb://localhost'
                      database='conftrak_test'+str(uuid.uuid4()), serviceport=7771,
                      tzone='US/Eastern')

try:
    from subprocess import DEVNULL # py3k only
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

def conftrak_setup():
    global proc
    env = os.environ.copy()
    f = os.path.dirname(os.path.realpath(__file__))
    proc = Popen([os.path.join(os.path.split(env["_"])[0], "python"),
                  "../../startup.py", "--mongo-uri",
                  testing_config["mongouri"], "--database",
                  testing_config['database'], "--timezone", testing_config['tzone'],
                  "--service-port", str(testing_config['serviceport'])]
                 , cwd=f, env=env, stdout=DEVNULL, stderr=STDOUT)
    print('Started the server with configuration..:{}'.format(testing_config))
    ttime.sleep(4) # make sure the process is started


def conftrak_teardown():
    proc2 = Popen(['kill', '-9', str(proc.pid)])
    ttime.sleep(5) # make sure the process is killed
    conn = MongoClient(host=testing_config['mongohost'],
                       port=testing_config['mongoport'])
    conn.drop_database(testing_config['database'])
    conn.close()
    ttime.sleep(2)

