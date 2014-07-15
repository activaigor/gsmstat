#!/usr/bin/python

from GSMStat import GSMStat
import os,traceback

gsmstat = GSMStat()
gsmstat.logSet("/usr/local/bin/gsmstat/debug.log" , "info")

try:
	gsmstat.run()
except Exception:
	traceback.print_exc(file=open("/usr/local/bin/gsmstat/error.log","a"))
