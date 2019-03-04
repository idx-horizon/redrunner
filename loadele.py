from src.utils import get_external_elevations
import main
import app.db
from app.db import DBO
import datetime
import json
from app import app, THISDB

mydb = DBO(THISDB)

with mydb:
    d = get_external_elevations()
    store = json.dumps(d)
    mydb.cur.execute('INSERT into reference values (?,?,?,?)',
                           ('elevations',
                            ''
                            ,store, datetime.datetime.now()))
    mydb.conn.commit()
    print('Saved %s elevation records' % (len(d,)))

