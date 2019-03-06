import os
import sqlite3
from app.models import User, Runner, Apple
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
		print('** Using', self.dbname)
		self.connectDB()
		
	def __exit__(self, *args):
		print('** Closing', self.dbname)
		self.disconnect()
		
	def createdb(self):
	
		con = sqlite3.connect(self.dbname)
		
		con.execute('''
			CREATE TABLE runner (
					rid char(10) not null, 
					public_flag bool, 
					fullname char(50) NOT NULL, 
					threshold char(10)
				)
				'''
				)
	
		con.commit()
		
		for thisrunner in {
			('184594',  'Ian',      '32:00', 1),
			('185368',  'Matt',     '25:00', 1),
			('4327482', 'Caroline', '34:00', 0),
			('2564629', 'Michael',  '25:00', 0),
			('23656',   'Eileen',   '34:00', 0),
			('3158074', 'Sam',      '30:00', 0),
			
		}:
			r = Runner(rid=thisrunner[0],
						fullname=thisrunner[1], 
						threshold=thisrunner[2], 
						public_flag=thisrunner[3]
						)
			flaskdb.session.add(r)
		flaskdb.session.commit()
		
		con.execute('''
			CREATE TABLE user (
					id integer PRIMARY KEY, 
					username char(50) not null, 
					email char(120), 
					password_hash char(128)
				)
				'''
				)
		 		
		con.commit()
		for thisuser in {'ian','matt','test'}:
			u = User(username=thisuser,email='tbc')
			flaskdb.session.add(u)
			
		flaskdb.session.commit()
		
		print('** Users: ', User.query.all())

		con.execute('CREATE TABLE reference (key CHAR(20), subkey CHAR(20), value BLOB, modified_date CHAR(30))')
		con.commit()
					
		print('** Created DB:', self.dbname)
		
	def deletedb(self):
		os.remove(self.dbname)
		print('**', self.dbname, ' - Database deleted')
		
	def getdata(self, sql):
		self.cur.execute(sql)
		return self.cur.fetchall()
		
