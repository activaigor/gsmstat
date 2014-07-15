#!/usr/bin/python
# -*- coding: utf-8 -*-
import MySQLdb

class MysqlFetch:
	""" Interface to fetch data from mysql database """ 

	def __init__(self, host='localhost', user='root', passwd='', db='', port=3306):
		self.host = host
		self.port = port
		self.user = user
		self.passwd = passwd
		self.db = db
        
	def query(self, query, charset="utf8"):
		db = MySQLdb.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd, db=self.db, compress=1)
		db.set_character_set(charset)
		cursor = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
		# If we have duplicate-primary set result=0
		try:
			cursor.execute(query)
			result=cursor.fetchall()
		except MySQLdb.IntegrityError:
			result=0
		cursor.close()
		db.commit()
		db.close()
		return result

if __name__ == '__main__':
	print 'This a module but not a programm'
