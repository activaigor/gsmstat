from mysqlfetch import MysqlFetch
from threading import Thread
import xmlrpclib
import ConfigParser
import re
import logging
import json
import time

class GSMStat():

	ami = None
	sql = None
	monitoring_thread = None
	config = ConfigParser.ConfigParser()
	config.read("/usr/local/bin/gsmstat/settings.ini")
	logger = logging.getLogger('GSMstat')
	operators = ["mtc","kyivstar"]

	def ami_connect(self):
		ami_port = self.config.get("ami" , "proxy_port")
		ami_host = self.config.get("ami" , "proxy_host")
		self.ami = xmlrpclib.ServerProxy("http://{host}:{port}".format(host = ami_host, port = ami_port))
		#self.ami.logout()
		#self.ami.loginNew("GSMstat","n3vJgpLk5UoF")

	def sql_connect(self):
		sql_host = self.config.get("mysql" , "host")
		sql_user = self.config.get("mysql" , "user")
		sql_pass = self.config.get("mysql" , "pass")
		sql_db = self.config.get("mysql" , "db")
		self.sql = MysqlFetch(host = sql_host , user = sql_user , passwd = sql_pass , db = sql_db)

	def logSet(self,pathInfo,logLevel):
		self.pathInfo=pathInfo
		self.logLevel=logLevel
		self.hdlr = logging.FileHandler(self.pathInfo)
		self.formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		self.hdlr.setFormatter(self.formatter)
		self.logger.addHandler(self.hdlr)
		if self.logLevel == "info":
			self.logger.setLevel(logging.INFO)
		elif self.logLevel == "warn":
			self.logger.setLevel(logging.WARNING)

	# Main loop here
	def run(self):
		self.ami_connect()
		self.sql_connect()
		self.ami.catch_event("Dial","GSMStat")
		self.ami.catch_event("Hangup","GSMStat")
		self.ami.catch_event("OriginateResponse","GSMStat")
		self.monitoring_thread = Thread(target = self._channel_monitor)
		self.monitoring_thread.start()
		while True:
			try:
				message = json.loads(self.ami.get_messages("GSMStat"))
				event = message["Event"]
				if (event == "Dial"):
					dialstatus = message["SubEvent"]
					if (dialstatus == "Begin"):
						for direction in self.operators:
							peer = self.peerFromMsg(direction,message["Channel"])
							if (peer != False):
								break
							peer = self.peerFromMsg(direction,message["Destination"])
							if (peer != False):
								break
						if (peer != False):
							self.sql.query("UPDATE gsm_channels SET status = 'busy' WHERE name = '{channel}'".format(channel = peer))
							self.logger.info("> " + peer)
				elif (event == "Hangup"):
					causetxt = message["Cause-txt"]
					cause = str(message["Cause"])
					for direction in self.operators:
						peer = self.peerFromMsg(direction,message["Channel"])
						if (peer != False):
							break
					if (peer != False):
						if (cause == "16" or cause == "21" or cause == "17" or cause == "0"):
							self.sql.query("UPDATE gsm_channels SET status = 'free', calls = calls + 1 WHERE name = '{channel}'".format(channel = peer))
						elif (cause == "34" or cause == "42"):
							self.sql.query("UPDATE gsm_channels SET status = 'problem' WHERE name = '{channel}'".format(channel = peer))
							self.logger.warning(str(peer) + " has circuit/busy")
						else:
							self.sql.query("UPDATE gsm_channels SET status = 'problem' WHERE name = '{channel}'".format(channel = peer))
							self.logger.warning("Unexpected hangup-cause")
							self.logger.warning(message)
						self.logger.info("< " + peer + " : " + str(causetxt))
				elif (event == "OriginateResponse" and str(message["Reason"]) == "4"):
					for direction in self.operators:
						peer = self.peerFromMsg(direction,message["Channel"])
						if (peer != False):
							break
					if (peer != False):
						self.sql.query("UPDATE gsm_channels SET status = 'busy' WHERE name = '{channel}'".format(channel = peer))
						self.logger.info("> " + peer + " [orig]")
			except Exception, err:
				print "Exception has occured while processing the message"
				print Exception, err
				print msg



	def _channel_monitor(self):
		while True:
			time.sleep(30)
			data = self.sql.query("SELECT * FROM gsm_channels WHERE status = 'problem' and UNIX_TIMESTAMP(stamp) + 60 <= UNIX_TIMESTAMP()")
			if len(data) > 0:
				for chan in data:
					self.logger.info("[ChanMonitor]: {name} has a problem. Lets check its condition".format(name = chan["name"]))
					self.ami.makeCall("SIP/"+str(chan["name"])+"/"+str(chan["prefix"])+"0445004339","0109")

	def peerFromChan(self,chan):
		found = re.search('.*SIP/(.+)-[^-]+', chan)
		if found:
			return found.group(1)
		else:
			return False

	def peerFromMsg(self,operator,text):
		found = re.search('.*SIP/(.*'+str(operator)+'.*)-[^-]+', text)
		if found:
			return found.group(1)
		else:
			return False
