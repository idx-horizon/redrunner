import os
import sqlite3
from app.models import User, Runner, Runnerlink, Reference
from app import flaskdb

class DBO:

	def __init__(self, dbname):
		self.dbname = dbname
		self.conn = None
		self.cur = None
		if os.path.isfile(dbname):
			print('**', dbname)
		else:
			print('**', dbname, 'does not exist')
			self.createdb()
			
	def dict_factory(self, cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
			
		return d
		
	def connectDB(self):
		self.conn = sqlite3.connect(self.dbname)
		self.cur = self.conn.cursor()
		self.ncur = self.conn.cursor()
		self.cur.row_factory = sqlite3.Row
		self.dcur = self.conn.cursor()
		self.dcur.row_factory = self.dict_factory
		
	def disconnect(self):
		self.cur.close()
		self.ncur.close()
		self.dcur.close()
		self.conn.close()
		
	def __enter__(self):
		#print('** Using', self.dbname)
		self.connectDB()
		
	def __exit__(self, *args):
		#print('** Closing', self.dbname)
		self.disconnect()
		
	def createdb(self):
	
		con = sqlite3.connect(self.dbname)
		
		con.execute('''
			CREATE TABLE runner (
					rid char(10) not null, 
					public_flag bool, 
					fullname char(50) NOT NULL, 
					threshold char(10),
					home_run char(50)
					)
			'''
		)
	
		con.commit()
		
		for thisrunner in {
			('184594',  'Ian',          '32:00', 1, 'Bromley'),
			('185368',  'Matt',         '25:00', 0, 'Bromley'),
			('4327482', 'Caroline',     '34:00', 0, 'Banstead Woods'),
			('2564629', 'Michael',      '25:00', 0, 'Riddlesdown'),
			('23656',   'Eileen',       '34:00', 0, 'Clair'),
			('3158074', 'Sam',          '30:00', 0, 'Shorne Woods'),
			('33202',   'Ant',          '21:00', 0, 'Fulham Palace'),
			('541276',  'Sharon',       '31:00', 0, 'Woking')
			
		}:
			r = Runner(rid=thisrunner[0],
						fullname=thisrunner[1], 
						threshold=thisrunner[2], 
						public_flag=thisrunner[3],
						home_run=thisrunner[4]
						)
						
			flaskdb.session.add(r)

		flaskdb.session.commit()
		
		con.execute('''
			CREATE TABLE user (
					id integer PRIMARY KEY, 
					username char(50) not null,
					rid char(10), 
					email char(120), 
					password_hash char(128),
					home_run char(50),
					home_postcode char(50)
					)
			'''
		)
		 		
		con.commit()

		for thisuser in {
			('ian',  '184594', 'Bromley', 'BR4 9NZ'),
			('caroline',   '4327482', 'Banstead Woods', None),
			('matt', '185368', 'Bromley', None),
			('michael', '2564629', 'Riddlesdown', None),
			('sam', '3158074', 'Shorne Woods', None),
			('eileen', '23656', 'Clair', None),
			('ant', '33202', 'Fulham Palace', None),
			('sharon', '541276', 'Woking', None)
		}:
			u = User(username=thisuser[0], 
						rid=thisuser[1], 
						email='tbc',
						home_run=thisuser[2],
						home_postcode=thisuser[3])
						
			u.set_password('p')
			flaskdb.session.add(u)
			
		flaskdb.session.commit()
		
		print('** Users: ', User.query.all())

		con.execute('''
			CREATE TABLE runnerlink (
					id integer PRIMARY KEY, 
					username char(50) not null,
					rid char(10) not null,
					added_date CHAR(30)	
					)
			'''
		)
		con.commit()

		for link in {
			('ian', '184594'), #self
			('ian', '185368'),
			('ian', '2564629'),
			('ian', '4327482'),
			('ian', '541276'),
			('matt', '185368'), #self
			('matt', '184594'),
			('caroline', '4327482'), #self
			('caroline', '184594'),
			('caroline', '23656'),
			('michael', '2564629'), #self
			('sharon', '541276'), #self
			('ant', '33202'), #self
			('eileen', '23656') #self
		}:
			l = Runnerlink(username=link[0], rid=link[1])
			flaskdb.session.add(l)

		flaskdb.session.commit()

		con.execute('''
			CREATE TABLE reference (
					id integer PRIMARY KEY, 
					key CHAR(20),
					subkey CHAR(20),
					value BLOB,
					modified_date CHAR(30)
					)
			'''
		)
		con.commit()
		
		with open('resources/elevations.dat','r') as fh:
			ele = fh.read()
		rec = Reference(key='elevations',value=ele.encode())		
		flaskdb.session.add(rec)
		flaskdb.session.commit()
			
					
		print('** Created DB:', self.dbname)
		
	def deletedb(self):
		os.remove(self.dbname)
		print('**', self.dbname, ' - Database deleted')
		
	def getdata(self, sql):
		self.cur.execute(sql)
		return self.cur.fetchall()
		
