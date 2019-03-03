from main import get_elevations
import main
import src.db
from src.db import DBO
import datetime
import json

mydb = DBO('REPOSITORY.db')

with mydb:
    d = main.get_external_elevations()
    store = json.dumps(d)
    mydb.cur.execute('INSERT into reference values (?,?,?,?)',
                                                   ('elevations',
                                                    ''
                                                    ,store, datetime.datetime.now()))
    mydb.conn.commit()
    print('Saved %s elevation records' % (len(d,)))

