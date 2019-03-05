import os
import sqlite3

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
	
		con = sqlite3.connect(self.dbname) # Warning: This file is created in the current directory

		
		con.execute('CREATE TABLE runner (rid char(10) not null, public_flag bool, fullname char(50) NOT NULL, threshold char(10))')
		con.execute('INSERT INTO runner (rid, public_flag, fullname, threshold) VALUES (\'184594\',1, \'Ian\', \'32:00\')')
		con.execute('INSERT INTO runner (rid, public_flag, fullname, threshold) VALUES (\'185368\', 1, \'Matt\', \'25:00\')')
		con.execute('INSERT INTO runner (rid, public_flag, fullname, threshold) VALUES (\'4327482\', 0, \'Caroline\', \'34:00\')')
		con.execute('INSERT INTO runner (rid, public_flag, fullname, threshold) VALUES (\'2564629\', 0, \'Michael\', \'25:00\')')		
		con.execute('INSERT INTO runner (rid, public_flag, fullname, threshold) VALUES (\'23656\', 0, \'Eileen\',\'34:00\')')
		con.execute('INSERT INTO runner (rid, public_flag, fullname, threshold) VALUES (\'3158074\', 0, \'Sam\', \'30:00\')')		
				
		con.commit()
		
		con.execute('CREATE TABLE user (username char(50) not null, email char(120), password_hash char(128))')
		con.execute('INSERT INTO user (usernname, email, password_hash) VALUES (\'Ian\',\'TBC\',\' \')')
		con.execute('INSERT INTO user (usernname, email, password_hash) VALUES (\'Test\',\'TBC\',\' \')')
		con.commit()
		
		con.execute('CREATE TABLE reference (key CHAR(20), subkey CHAR(20), value BLOB, modified_date CHAR(30))')
		con.commit()
					
		print('** Created DB:', self.dbname)
		
	def deletedb(self):
		os.remove(self.dbname)
		print('**', self.dbname, ' - Database deleted')
		
	def getdata(self, sql):
		self.cur.execute(sql)
		return self.cur.fetchall()
		
