from flask import Flask
from app.utils import get_external_elevations, check_url_status
from app.db import DBO
import datetime
import json
from app import app, THISDB
from app.config import Config

app = Flask(__name__, template_folder='../templates')


app.config.from_object(Config)
print(app.config)

mydb = DBO(THISDB)

with mydb:
    d = get_external_elevations(app)
    store = json.dumps(d)
    mydb.cur.execute('INSERT into reference (key, subkey, value, modified_date) values (?,?,?,?)',
                           ('elevations',
                            ''
                            ,store,
                            datetime.datetime.now()))
    mydb.conn.commit()
    print('Saved %s elevation records' % (len(d,)))

