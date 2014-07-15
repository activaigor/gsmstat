#!/usr/bin/python

import xmlrpclib
import sys
import re
import time
import datetime
from django.utils.encoding import smart_str

def messageCut(toFind,amiMessage):
        for amiString in smart_str(amiMessage).split("\n"):
                try:
                        if amiString.split(" ")[0] == toFind+":":
                                return amiString.split(" ")[1]
                except IndexError:
                        break
        return 0


ami = xmlrpclib.ServerProxy("http://localhost:8125")
#ami.loginNew("GSMstat","n3vJgpLk5UoF")
#ami.prepareChannel("mtc","1-2-3-4-1-2-1-2","0-0-0-0-0-0-30-31")
#ami.prepareChannel("kyivstar","---1-2-3-4","0-0-0-0-0-36-37")
#ami.prepareChannel("mtc","1-2-3-4-1-2-3-4","2-43-44-45-46-0-30-31")
#ami.prepareChannel("kyivstar","---1-2-3-4","0-6-19-0-35-36-37")

def peerFromMsg(operator,text):
	found = re.search('.*SIP/(.*'+str(operator)+'.*)-[^-]+', text)
	if found:
		return found.group(1)
	else:
		return False

while True:
	msg = ami.eventSearch("Dial|Hangup|OriginateResponse")
	message = msg[0]
	event = msg[1]
	if (event == "Dial"):
		print message
		dialstatus = messageCut("SubEvent",message)
		if (dialstatus == "Begin"):
			print peerFromMsg("mtc",message)
	elif (event == "Hangup"):
		print message
		#print message
		print peerFromMsg("mtc",message)
